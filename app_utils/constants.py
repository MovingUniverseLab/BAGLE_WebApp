
################################################
# Packages
################################################
import pandas as pd


################################################
# BAGLE Configurations
################################################
# List of model parameterizations
PSPL = (
    'PSPL_Phot_noPar_Param1', 'PSPL_Phot_noPar_Param2', 
    
    'PSPL_Phot_Par_Param1', 'PSPL_Phot_Par_Param2',
    
    'PSPL_Phot_noPar_GP_Param1', 'PSPL_Phot_noPar_GP_Param2',
    
    'PSPL_Phot_Par_GP_Param1', 'PSPL_Phot_Par_GP_Param1_2', 
    'PSPL_Phot_Par_GP_Param2', 'PSPL_Phot_Par_GP_Param2_2', 'PSPL_Phot_Par_GP_Param2_3', 'PSPL_Phot_Par_GP_Param2_4', 'PSPL_Phot_Par_GP_Param2_5',
    
    'PSPL_Astrom_Par_Param3', 'PSPL_Astrom_Par_Param4',
    
    'PSPL_PhotAstrom_noPar_Param1', 'PSPL_PhotAstrom_noPar_Param2', 'PSPL_PhotAstrom_noPar_Param3', 
    'PSPL_PhotAstrom_noPar_Param4', 
    
    'PSPL_PhotAstrom_noPar_GP_Param1', 'PSPL_PhotAstrom_noPar_GP_Param2',
    
    'PSPL_PhotAstrom_Par_Param1', 'PSPL_PhotAstrom_Par_Param2', 'PSPL_PhotAstrom_Par_Param3', 
    'PSPL_PhotAstrom_Par_Param4', 'PSPL_PhotAstrom_Par_Param5',
    
    'PSPL_PhotAstrom_Par_GP_Param1', 'PSPL_PhotAstrom_Par_GP_Param2', 
    'PSPL_PhotAstrom_Par_GP_Param3', 'PSPL_PhotAstrom_Par_GP_Param3_1', 'PSPL_PhotAstrom_Par_GP_Param3_2',
    'PSPL_PhotAstrom_Par_GP_Param4', 'PSPL_PhotAstrom_Par_GP_Param4_1', 'PSPL_PhotAstrom_Par_GP_Param4_2',
)

# PSPL + GP currently errored in BAGLE
PSBL = (
    'PSBL_Phot_noPar_Param1', 
    
    'PSBL_Phot_Par_Param1',
    
    'PSBL_Phot_noPar_GP_Param1', 
    
    'PSBL_Phot_Par_GP_Param1',
    
    'PSBL_PhotAstrom_noPar_Param1', 'PSBL_PhotAstrom_noPar_Param2', 'PSBL_PhotAstrom_noPar_Param3',
    'PSBL_PhotAstrom_Par_Param1', 'PSBL_PhotAstrom_Par_Param2', 'PSBL_PhotAstrom_Par_Param3', 'PSBL_PhotAstrom_Par_Param7',
    
    'PSBL_PhotAstrom_noPar_GP_Param1', 'PSBL_PhotAstrom_noPar_GP_Param2',
    
    'PSBL_PhotAstrom_Par_GP_Param1', 'PSBL_PhotAstrom_Par_GP_Param2'
)

BSPL = (
    'BSPL_Phot_noPar_Param1', 
    
    'BSPL_Phot_Par_Param1',
    
    'BSPL_Phot_noPar_GP_Param1',
    
    'BSPL_Phot_Par_GP_Param1',
    
    'BSPL_PhotAstrom_noPar_Param1', 'BSPL_PhotAstrom_noPar_Param2', 'BSPL_PhotAstrom_noPar_Param3',
    
    'BSPL_PhotAstrom_Par_Param1', 'BSPL_PhotAstrom_Par_Param2', 'BSPL_PhotAstrom_Par_Param3',
    
    'BSPL_PhotAstrom_noPar_GP_Param1', 'BSPL_PhotAstrom_noPar_GP_Param2', 'BSPL_PhotAstrom_noPar_GP_Param3',
    
    'BSPL_PhotAstrom_Par_GP_Param1', 'BSPL_PhotAstrom_Par_GP_Param2', 'BSPL_PhotAstrom_Par_GP_Param3'
)

BSBL = (
    'BSBL_PhotAstrom_noPar_Param1', 'BSBL_PhotAstrom_noPar_Param2',
    
    'BSBL_PhotAstrom_Par_Param1', 'BSBL_PhotAstrom_Par_Param2'
)

ALL_MODS = PSPL + PSBL + BSPL + BSBL

# Dictionary for default slider ranges of model parameters
    # Note: the list order is (Units, Default, Min, Max, Step)
DEFAULT_RANGES = {
    'Time': ('MJD', 56500, 54500, 56500, 0.1),

    'alpha': ('deg', 5, 0, 90, 0.1),
    'alphaL': ('deg', 5, 0, 90, 0.1),
    'alphaS': ('deg', 5, 0, 90, 0.1),
    'b_sff': (None, 0.75, 0, 1.5, 0.1),
    'beta': ('mas', 0.2, -2, 2, 0.01),
    'beta_p': ('mas', 0.2, -2, 2, 0.01),
    'decL': ('deg', 29.008, -90, 90, 0.01),
    'dL': ('pc', 3500, 1000, 8000, 0.1),
    'dL_dS': (None, 0.5, 0.01, 0.999, 0.01),
    'dS': ('pc', 5000, 100, 10000, 0.1),
    'fratio_bin': (None, 0.3, 0.01, 1.5, 0.01),
    'gp_log_S0': (None, -8.5, -15, 5, 0.1),
    'gp_log_omega0': ('log(1/days)', 1, -10, 10, 0.1),
    'gp_log_omega04_S0': (None, -8.5, -15, 5, 0.1),
    'gp_log_omega0_S0': (None, -10, -15, 5, 0.1),
    'gp_log_rho': ('log(days)', 1.3, -2, 2, 0.1),
    'gp_rho': ('days', 20, 0.01, 100, -0.1),
    'gp_log_sigma': (None, -4, -10, 5, 0.1),
    'gp_log_jit_sigma': (None, -4.5, -10, 5, 0.1),
    'log10_thetaE': ('log10(mas)', 0.5, -1, 1, 0.1),
    'mL': ('Msun', 10, 0.1, 100, 0.1),
    'mLp': ('Msun', 10, 0.1, 100, 0.1),
    'mLs': ('Msun', 10, 0.1, 100, 0.1),
    'mag_base': ('mag', 19, 14, 24, 0.1),
    'mag_src': ('mag', 19, 14, 24, 0.1),
    'mag_src_pri':('mag', 19, 14, 24, 0.1),
    'mag_src_sec': ('mag', 19, 14, 24, 0.1),
    'muL_E': ('mas/yr', 0, -20, 20, 0.1),
    'muL_N': ('mas/yr', 0, -20, 20, 0.1),
    'muS_E': ('mas/yr', 2, -20, 20, 0.1),
    'muS_N': ('mas/yr', 0, -20, 20, 0.1),
    'phi': ('deg', 10, 0, 90, 0.1),
    'piEN_piEE': (None, 1, -2, 2, 0.01),
    'piE_E': ('thetaE', 0.05, -1.0, 1.0, 0.01),
    'piE_N': ('thetaE', 0.05, -1.0, 1.0, 0.01),
    'piS': ('mas', 0.12, 0.01, 1.0, 0.1),
    'q': (None, 1, 0.1, 5, 0.1),
    'raL': ('deg', 266.417, 0, 360, 0.01),
    'sep': ('mas', 5, 0.5, 10, 0.1),
    'sepL': ('mas', 5, 0.5, 10, 0.1),
    'sepS': ('mas', 5, 0.5, 10, 0.1),
    't0': ('MJD', 55500, 55000, 56000, 0.1),
    't0_p': ('MJD', 55500, 55000, 56000, 0.1),
    't0_prim': ('MJD', 55500, 55000, 56000, 0.1),
    'tE': ('days', 200.0, 1.0, 400.0, 0.1),
    'thetaE': ('mas', 2.0, 0.0, 10.0, 0.1),
    'u0_amp': ('thetaE', 0.5, -1.0, 1.0, 0.1),
    'u0_amp_prim': ('thetaE', 0.5, -1.0, 1.0, 0.1),
    'xS0_E': ('arcsec', 1.0, -5.0, 5.0, 0.1),
    'xS0_N': ('arcsec', 1.0, -5.0, 5.0, 0.1),

    'alphaL_rad': ('rad', None, None, None, None),
    'alphaS_rad': ('rad', None, None, None, None),
    'alpha_rad': ('rad', None, None, None, None),
    'm1': ('arcsec^2', None, None, None, None),
    'm2': ('arcsec^2', None, None, None, None),
    'muL': ('mas/yr', None, None, None, None),
    'muRel': ('mas/yr', None, None, None, None),
    'muRel_E': ('mas/yr', None, None, None, None),
    'muRel_N': ('mas/yr', None, None, None, None),
    'muRel_amp': ('mas/yr', None, None, None, None),
    'muRel_hat': ('mas/yr', None, None, None, None),
    'muS': ('mas/yr', None, None, None, None),
    'phiL': ('deg', 10, 0, 90, 0.1),
    'phiL_rad': ('rad', None, None, None, None),
    'phi_piE': ('deg', None, None, None, None),
    'phi_piE_rad': ('rad', None, None, None, None),
    'phi_rad': ('rad', None, None, None, None),
    'phi_rho1_rad': ('rad', None, None, None, None),
    'piE': ('thetaE', None, None, None, None),
    'piE_amp': ('thetaE', None, None, None, None),
    'piL': ('mas', None, None, None, None),
    'piRel': ('mas', None, None, None, None),
    't0_pri': ('MJD', None, None, None, None),
    't0_sec': ('MJD', None, None, None, None),
    'thetaE_E': ('mas', None, None, None, None),
    'thetaE_N': ('mas', None, None, None, None),
    'thetaE_amp': ('mas', None, None, None, None),
    'thetaE_hat': ('mas', None, None, None, None),
    'thetaS0': ('mas', None, None, None, None),
    'u0': ('thetaE', None, None, None, None),
    'u0_amp_p': ('thetaE', None, None, None, None),
    'u0_amp_pri': ('thetaE', None, None, None, None),
    'u0_amp_sec': ('thetaE', None, None, None, None),
    'u0_hat': ('thetaE', None, None, None, None),
    'u0_hat_p': ('thetaE', None, None, None, None),
    'u0_p': ('thetaE', None, None, None, None),
    'u0_pri': ('thetaE', None, None, None, None),
    'u0_sec': ('thetaE', None, None, None, None),
    'xL0': ('arcsec', None, None, None, None),
    'xL0_E': ('arcsec', None, None, None, None),
    'xL0_N': ('arcsec', None, None, None, None),
    'xL1_over_theta': (None, None, None, None, None),
    'xL2_over_theta': (None, None, None, None, None),
    'xS0': ('arcsec', None, None, None, None),
    'xS0_pri': ('arcsec', None, None, None, None),
    'xS0_sec': ('arcsec', None, None, None, None)
}

DEFAULT_DF = pd.DataFrame.from_dict(DEFAULT_RANGES, orient = 'index')
DEFAULT_DF.columns = ['Units', 'Value', 'Min', 'Max', 'Step']
DEFAULT_DF.index.name = 'Parameter'

# Default Data frames for slider settinsg and parameter values
DEFAULT_SLIDER_DF = DEFAULT_DF[['Units','Min', 'Max', 'Step']]
DEFAULT_PARAM_DF = DEFAULT_DF[['Units', 'Value']]