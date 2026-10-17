import unittest,json,io,zipfile,tempfile,lzma,struct
from pathlib import Path
import numpy as np
import pandas as pd
from diffusion.statistics import ols_hc3,wild_band,pca_fit,pca_transform,fit_adjustment,response_function,adjustment_diagnostics,paired_mse_summary
from diffusion.histdata import decode_year,align_frame,source_clock_to_utc
from diffusion.data import decode_candles
from diffusion.empirical import panel,return_between
from diffusion.common import ROOT,sha256

class ResearchChecks(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(912);self.x=np.c_[np.ones(30),rng.normal(size=30)];self.y=2+3*self.x[:,1]+rng.normal(size=30)*(1+abs(self.x[:,1]))
    def test_ols_matches_independent_normal_equations(self):
        actual=ols_hc3(self.x,self.y)['coef'][:,0]
        expected=np.linalg.solve(self.x.T@self.x,self.x.T@self.y)
        np.testing.assert_allclose(actual,expected,atol=1e-12)
    def test_hc3_matches_leave_one_out_influence(self):
        f=ols_hc3(self.x,self.y);b=f['coef'][:,0];cov=np.zeros((2,2))
        for i in range(len(self.y)):
            k=np.arange(len(self.y))!=i;bi=np.linalg.lstsq(self.x[k],self.y[k],rcond=None)[0];d=bi-b;cov+=np.outer(d,d)
        np.testing.assert_allclose(f['cov'][0],cov,rtol=1e-10,atol=1e-12)
    def test_rank_failure_is_explicit(self):
        with self.assertRaises(ValueError):ols_hc3(np.ones((30,2)),self.y)
    def test_nonfinite_is_rejected(self):
        y=self.y.copy();y[0]=np.nan
        with self.assertRaises(ValueError):ols_hc3(self.x,y)
    def test_wild_bootstrap_reproducible_and_shared_path(self):
        f=ols_hc3(self.x,np.c_[self.y,2*self.y]);a=wild_band(f,reps=99);b=wild_band(f,reps=99)
        np.testing.assert_equal(a['draws'],b['draws']);np.testing.assert_allclose(a['draws'][:,1],2*a['draws'][:,0],atol=1e-10)
    def test_pca_unit_training_scale(self):
        r=np.random.default_rng(123).normal(size=(40,5));m=pca_fit(r);z=pca_transform(r,m)
        self.assertAlmostEqual(z.mean(),0,12);self.assertAlmostEqual(z.std(ddof=1),1,12);self.assertGreaterEqual(sum(m['loadings']),0)
    def test_future_data_cannot_recentre_frozen_pca(self):
        r=np.random.default_rng(5).normal(size=(40,5));m=pca_fit(r);before=pca_transform(r,m);pca_transform(np.ones((5,5))*1000,m)
        np.testing.assert_equal(before,pca_transform(r,m))
    def test_clean_diffusion_parameter_recovery(self):
        h=np.arange(1,21);m=fit_adjustment(h,response_function(h,-25,.25,.22))
        np.testing.assert_allclose([m['amplitude_bps'],m['first_minute_fraction'],m['k_per_minute']],[-25,.25,.22],atol=1e-6)
    def test_t90_formula_reaches_threshold(self):
        m=fit_adjustment(np.arange(1,21),response_function(np.arange(1,21),25,.25,.22))
        self.assertAlmostEqual(response_function(m['t90_minutes'],25,.25,.22)/25,.9,10)
    def test_zero_response_has_no_speed(self):
        self.assertFalse(fit_adjustment(np.arange(1,21),np.zeros(20))['success'])
    def test_reversal_is_not_monotone_diffusion(self):
        m=fit_adjustment(np.arange(1,21),-10-30*np.exp(-np.arange(20)/4))
        self.assertTrue(m['boundary'] or m['normalised_rmse']>.25)
    def test_timestamp_dst_and_fixed_est(self):
        winter=pd.Timestamp('2022-01-26 14:00',tz='America/New_York').tz_convert('UTC');summer=pd.Timestamp('2022-06-15 14:00',tz='America/New_York').tz_convert('UTC')
        self.assertEqual(winter.hour,19);self.assertEqual(summer.hour,18)
        source=pd.Timestamp('2022-06-15 13:00',tz='Etc/GMT+5').tz_convert('UTC');self.assertEqual(source,summer)
    def test_csv_decoder_ohlc_and_timezone(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'example.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('x.csv','20220615 130000;100;102;99;101;0\n20220615 130100;100;99;98;101;0\n')
            d=decode_year(p);self.assertEqual(d.index[0],pd.Timestamp('2022-06-15 17:00Z'));self.assertTrue(d.valid.iloc[0]);self.assertFalse(d.valid.iloc[1])
            original=decode_year(p,clock='documented_est');self.assertEqual(original.index[0],pd.Timestamp('2022-06-15 18:00Z'))
    def test_audited_clock_matches_independent_boundary_probes(self):
        stamps=pd.Series(['20220316 130000','20220921 140000','20221102 130000','20220126 140000'])
        out=source_clock_to_utc(stamps)
        expected=pd.to_datetime(['2022-03-16 18:00Z','2022-09-21 18:00Z','2022-11-02 18:00Z','2022-01-26 19:00Z'])
        self.assertEqual(out.tolist(),expected.tolist())
    def test_clock_correction_does_not_change_prices(self):
        stamps=pd.Series(['20220316 130000','20220921 140000'])
        delta=source_clock_to_utc(stamps,'documented_est')-source_clock_to_utc(stamps)
        self.assertEqual(delta.dt.total_seconds().tolist(),[0,3600])
    def test_duplicate_quotes_are_invalid(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'example.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('x.csv','20220615 130000;100;102;99;101;0\n'*2)
            self.assertFalse(decode_year(p).valid.iloc[0])
    def test_alignment_never_fills_missing_minutes(self):
        t=pd.Timestamp('2022-06-15 18:00Z');idx=t+pd.to_timedelta(np.arange(-61,120),unit='m');d=pd.DataFrame({'close':100.,'valid':True},index=idx)
        self.assertEqual(len(align_frame(d,t)),181)
        with self.assertRaises(ValueError):align_frame(d.drop(t+pd.Timedelta(minutes=7)),t)
    def test_horizon_one_is_first_completed_minute(self):
        offsets=np.arange(-61,120);b=pd.DataFrame({'event_id':'a','asset':'SPX','kind':'event','offset':offsets,'close':100*np.exp((offsets+1)/10000)})
        e=pd.DataFrame({'event_type':['Statements'],'surprise':[1.],'date':['2022-06-15']},index=['a']);x,y,m,p=panel(b,e,'SPX','Statements')
        np.testing.assert_allclose(y[0],np.arange(1,21),atol=1e-10);np.testing.assert_allclose(return_between(p,5,20),15,atol=1e-10)
    def test_dukascopy_binary_order(self):
        b=lzma.compress(struct.pack('>5If',0,100000,101000,99000,102000,1.))
        d=decode_candles(b,'2017-01-02');self.assertEqual(d.close.iloc[0],101);self.assertEqual(d.high.iloc[0],102);self.assertTrue(d.valid.iloc[0])
    def test_paired_prediction_error_sign(self):
        s=paired_mse_summary(np.arange(10),np.arange(10),np.zeros(10),reps=99)
        self.assertLess(s['difference'],0);self.assertEqual(s['model_mse'],0)
    def test_original_protocol_and_amendment_hashes(self):
        for name in ['design-v1','amendment-01','amendment-02']:
            lock=json.loads((ROOT/f'protocol/{name}-lock.json').read_text());self.assertEqual(lock['sha256'],sha256(ROOT/f'protocol/{name}.json'))

if __name__=='__main__':unittest.main(verbosity=2)
