################################################
# BAGLE Configurations
################################################
# List of model parameterizations
PSPL = [
    'PSPL_Phot_noPar_Param1', 'PSPL_Phot_noPar_Param2', 
    
    'PSPL_Phot_Par_Param1', 'PSPL_Phot_Par_Param2',
    
    'PSPL_Phot_noPar_GP_Param1', 'PSPL_Phot_noPar_GP_Param2',
    
    'PSPL_Phot_Par_GP_Param1', 'PSPL_Phot_Par_GP_Param1_2', 
    'PSPL_Phot_Par_GP_Param2', 'PSPL_Phot_Par_GP_Param2_2', 'PSPL_Phot_Par_GP_Param2_3',
    
    'PSPL_Astrom_Par_Param3', 'PSPL_Astrom_Par_Param4',
    
    'PSPL_PhotAstrom_noPar_Param1', 'PSPL_PhotAstrom_noPar_Param2', 'PSPL_PhotAstrom_noPar_Param3', 
    'PSPL_PhotAstrom_noPar_Param4', 
    
    'PSPL_PhotAstrom_noPar_GP_Param1', 'PSPL_PhotAstrom_noPar_GP_Param2',
    
    'PSPL_PhotAstrom_Par_Param1', 'PSPL_PhotAstrom_Par_Param2', 'PSPL_PhotAstrom_Par_Param3', 
    'PSPL_PhotAstrom_Par_Param4', 'PSPL_PhotAstrom_Par_Param5',
    
    'PSPL_PhotAstrom_Par_GP_Param1', 'PSPL_PhotAstrom_Par_GP_Param2', 
    'PSPL_PhotAstrom_Par_GP_Param3', 'PSPL_PhotAstrom_Par_GP_Param3_1',
    'PSPL_PhotAstrom_Par_GP_Param4',
]

# PSPL + GP currently errored in BAGLE
PSBL = [
    'PSBL_Phot_noPar_Param1', 
    
    'PSBL_Phot_Par_Param1',
    
    'PSBL_Phot_noPar_GP_Param1', 
    
    'PSBL_Phot_Par_GP_Param1',
    
    'PSBL_PhotAstrom_noPar_Param1', 'PSBL_PhotAstrom_noPar_Param2', 'PSBL_PhotAstrom_noPar_Param3',
    'PSBL_PhotAstrom_Par_Param1', 'PSBL_PhotAstrom_Par_Param2', 'PSBL_PhotAstrom_Par_Param3', 'PSBL_PhotAstrom_Par_Param7',
    
    'PSBL_PhotAstrom_noPar_GP_Param1', 'PSBL_PhotAstrom_noPar_GP_Param2',
    
    'PSBL_PhotAstrom_Par_GP_Param1', 'PSBL_PhotAstrom_Par_GP_Param2'
]

BSPL = [
    'BSPL_Phot_noPar_Param1', 
    
    'BSPL_Phot_Par_Param1',
    
    'BSPL_Phot_noPar_GP_Param1',
    
    'BSPL_Phot_Par_GP_Param1',
    
    'BSPL_PhotAstrom_noPar_Param1', 'BSPL_PhotAstrom_noPar_Param2', 'BSPL_PhotAstrom_noPar_Param3',
    
    'BSPL_PhotAstrom_Par_Param1', 'BSPL_PhotAstrom_Par_Param2', 'BSPL_PhotAstrom_Par_Param3',
    
    'BSPL_PhotAstrom_noPar_GP_Param1', 'BSPL_PhotAstrom_noPar_GP_Param2', 'BSPL_PhotAstrom_noPar_GP_Param3',
    
    'BSPL_PhotAstrom_Par_GP_Param1', 'BSPL_PhotAstrom_Par_GP_Param2', 'BSPL_PhotAstrom_Par_GP_Param3'
]

BSBL = [
    'BSBL_PhotAstrom_noPar_Param1', 'BSBL_PhotAstrom_noPar_Param2',
    
    'BSBL_PhotAstrom_Par_Param1', 'BSBL_PhotAstrom_Par_Param2'
]

ALL_MODS = PSPL + PSBL + BSPL + BSBL

# Dictionary for default slider ranges of model parameters
    # Note: the list order is [Units, Default, Min, Max, Step]
DEFAULT_RANGES = {
    'Time': ['MJD', 56500, 54500, 56500, 0.1],

    'alpha': ['deg', 5, 0, 90, 0.1],
    'alphaL': ['deg', 5, 0, 90, 0.1],
    'alphaS': ['deg', 5, 0, 90, 0.1],
    'b_sff': [None, 0.75, 0, 1.5, 0.1],
    'beta': ['mas', 0.2, -2, 2, 0.01],
    'beta_p': ['mas', 0.2, -2, 2, 0.01],
    'decL': ['deg', 30, -90, 90, 0.1],
    'dL': ['pc', 3500, 1000, 8000, 0.1],
    'dL_dS': [None, 0.5, 0.01, 0.999, 0.01],
    'dS': ['pc', 5000, 100, 10000, 0.1],
    'fratio_bin': [None, 0.3, 0.01, 1.5, 0.01],
    'gp_log_S0': [None, -8.5, -15, 5, 0.1],
    'gp_log_omega0': ['log(1/days)', 1, -10, 10, 0.1],
    'gp_log_omega04_S0': [None, -8.5, -15, 5, 0.1],
    'gp_log_omega0_S0': [None, -10, -15, 5, 0.1],
    'gp_log_rho': ['log(days)', 1.3, -2, 2, 0.1],
    'gp_log_sigma': [None, -4, -10, 10, 0.1],
    'gp_rho': ['days', 20, 0.01, 100, -0.1],
    'log10_thetaE': ['log10(mas)', 0.5, -1, 1, 0.1],
    'mL': ['Msun', 10, 0.1, 100, 0.1],
    'mLp': ['Msun', 10, 0.1, 100, 0.1],
    'mLs': ['Msun', 10, 0.1, 100, 0.1],
    'mag_base': ['mag', 19, 14, 24, 0.1],
    'mag_src': ['mag', 19, 14, 24, 0.1],
    'mag_src_pri':['mag', 19, 14, 24, 0.1],
    'mag_src_sec': ['mag', 19, 14, 24, 0.1],
    'muL_E': ['mas/yr', 0, -20, 20, 0.1],
    'muL_N': ['mas/yr', 0, -20, 20, 0.1],
    'muS_E': ['mas/yr', 2, -20, 20, 0.1],
    'muS_N': ['mas/yr', 0, -20, 20, 0.1],
    'phi': ['deg', 10, 0, 90, 0.1],
    'piEN_piEE': [None, 1, -2, 2, 0.01],
    'piE_E': ['thetaE', 0.05, -1.0, 1.0, 0.01],
    'piE_N': ['thetaE', 0.05, -1.0, 1.0, 0.01],
    'piS': ['mas', 0.12, 0.01, 1.0, 0.1],
    'q': [None, 1, 0.1, 5, 0.1],
    'raL': ['deg', 50, 0, 360, 0.1],
    'sep': ['mas', 5, 0.5, 10, 0.1],
    'sepL': ['mas', 5, 0.5, 10, 0.1],
    'sepS': ['mas', 5, 0.5, 10, 0.1],
    't0': ['MJD', 55500, 55000, 56000, 0.1],
    't0_p': ['MJD', 55500, 55000, 56000, 0.1],
    't0_prim': ['MJD', 55500, 55000, 56000, 0.1],
    'tE': ['days', 200.0, 1.0, 400.0, 0.1],
    'thetaE': ['mas', 2.0, 0.0, 10.0, 0.1],
    'u0_amp': ['thetaE', 0.5, -1.0, 1.0, 0.1],
    'u0_amp_prim': ['thetaE', 0.5, -1.0, 1.0, 0.1],
    'xS0_E': ['arcsec', 1.0, -5.0, 5.0, 0.1],
    'xS0_N': ['arcsec', 1.0, -5.0, 5.0, 0.1],

    'alphaL_rad': ['rad', None, None, None, None],
    'alphaS_rad': ['rad', None, None, None, None],
    'alpha_rad': ['rad', None, None, None, None],
    'm1': ['arcsec^2', None, None, None, None],
    'm2': ['arcsec^2', None, None, None, None],
    'muL': ['mas/yr', None, None, None, None],
    'muRel': ['mas/yr', None, None, None, None],
    'muRel_E': ['mas/yr', None, None, None, None],
    'muRel_N': ['mas/yr', None, None, None, None],
    'muRel_amp': ['mas/yr', None, None, None, None],
    'muRel_hat': ['mas/yr', None, None, None, None],
    'muS': ['mas/yr', None, None, None, None],
    'phiL': ['deg', 10, 0, 90, 0.1],
    'phiL_rad': ['rad', None, None, None, None],
    'phi_piE': ['deg', None, None, None, None],
    'phi_piE_rad': ['rad', None, None, None, None],
    'phi_rad': ['rad', None, None, None, None],
    'phi_rho1_rad': ['rad', None, None, None, None],
    'piE': ['thetaE', None, None, None, None],
    'piE_amp': ['thetaE', None, None, None, None],
    'piL': ['mas', None, None, None, None],
    'piRel': ['mas', None, None, None, None],
    't0_pri': ['MJD', None, None, None, None],
    't0_sec': ['MJD', None, None, None, None],
    'thetaE_E': ['mas', None, None, None, None],
    'thetaE_N': ['mas', None, None, None, None],
    'thetaE_amp': ['mas', None, None, None, None],
    'thetaE_hat': ['mas', None, None, None, None],
    'thetaS0': ['mas', None, None, None, None],
    'u0': ['thetaE', None, None, None, None],
    'u0_amp_p': ['thetaE', None, None, None, None],
    'u0_amp_pri': ['thetaE', None, None, None, None],
    'u0_amp_sec': ['thetaE', None, None, None, None],
    'u0_hat': ['thetaE', None, None, None, None],
    'u0_hat_p': ['thetaE', None, None, None, None],
    'u0_p': ['thetaE', None, None, None, None],
    'u0_pri': ['thetaE', None, None, None, None],
    'u0_sec': ['thetaE', None, None, None, None],
    'xL0': ['arcsec', None, None, None, None],
    'xL0_E': ['arcsec', None, None, None, None],
    'xL0_N': ['arcsec', None, None, None, None],
    'xL1_over_theta': [None, None, None, None, None],
    'xL2_over_theta': [None, None, None, None, None],
    'xS0': ['arcsec', None, None, None, None],
    'xS0_pri': ['arcsec', None, None, None, None],
    'xS0_sec': ['arcsec', None, None, None, None]
}


################################################
# Panel Configurations
################################################
# Page colors
GP_ALPHA = 0.7
CLRS = {
    'main': 'rgb(18, 18, 18)',
    'secondary': 'rgb(43, 48, 53)',
    'light': 'rgb(75, 255, 239)',
    'selected': 'rgb(101, 175, 233)',
    'gridline': 'rgb(102, 102, 102)',
    'gp_cycle': [f'rgba(34, 255, 167, {GP_ALPHA})',
                 f'rgba(246, 249, 38, {GP_ALPHA})',
                 f'rgba(238, 166, 251, {GP_ALPHA})',
                 f'rgba(201, 251, 229, {GP_ALPHA})',
                 f'rgba(0, 181, 247, {GP_ALPHA})',
                 f'rgba(227, 238, 158, {GP_ALPHA})',
                 f'rgba(252, 105, 85, {GP_ALPHA})',
                 f'rgba(134, 206, 0, {GP_ALPHA})',
                 f'rgba(110, 137, 156, {GP_ALPHA})',
                 f'rgba(15, 133, 84, {GP_ALPHA})']
}

# Dictionary for font sizes
FONTSIZES = {
    'page_title':' 1.6rem',
    'header': '1.4rem',
    'paramztn_error': '1.4rem',
    'dropdown': '0.7rem',
    'plus': '0.8rem',
    'btn': '0.7rem',
    'slider': '0.8rem',
    'table_title': '0.75rem',
    'table_txt': '0.75rem',
    'error_title': '1.5rem',
    'error_txt': '1rem',
    'tooltip': '0.7rem',
    'summary_txt': '0.95rem',
    'plot_axes_ticks': 10,
    'plot_axes_labels': 14,
    'plot_title': 16,
    'legendgroup': 10
}

# CSS stylesheet for drop down menus
DROPDOWN_STYLE = '''
    select.bk-input {
        font-size: %s;
        text-align: center;
        border: white solid 0.08rem;
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
'''%(FONTSIZES['dropdown'])

# CSS stylesheet for push buttons
BASE_BTN_STYLE = '''
    :host {
        --design-primary-color: %s;
        margin: 0.4rem;
        flex-grow: 1;
    }
    
    :host(.solid) .bk-btn {
        color: white;
        border: 0.08rem solid white;
        border-radius: 0.8rem;
        font-size: %s;
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    } 
    
    :host(.solid) .bk-btn:hover {
        color: %s;
        border-color: %s;
    }
'''%(CLRS['secondary'], FONTSIZES['btn'], CLRS['light'], CLRS['light'])

SELECTED_BTN_STYLE = '''
    :host {
        --design-primary-color: %s;
        margin: 0.4rem;
        flex-grow: 1;
    }
    
    :host(.solid) .bk-btn {
        color: %s;
        border: 0.08rem solid %s;
        border-radius: 0.8rem;
        font-size: %s;
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    } 
    
'''%(CLRS['main'], CLRS['selected'], CLRS['selected'], FONTSIZES['btn'])

# CSS stylesheet for sliders
BASE_SLIDER_STYLE = '''
    :host {
        --design-primary-color: %s;
        --design-secondary-color: %s;
    }
    
    .bk-slider-title {
        font-size: %s;
    }
'''%(CLRS['light'], CLRS['main'], FONTSIZES['slider'])

ERRORED_SLIDER_STYLE = '''
    :host {
        --design-primary-color: red;
        --design-secondary-color: %s;
    }
    
    .bk-slider-title {
        color: red;
        font-size: %s;
    }
'''%(CLRS['main'], FONTSIZES['slider'])

# CSS stylesheet for tabulator
TABLTR_STYLE = '''
    .tabulator-col-title {
        font-size: %s;
    }
    
    .tabulator-cell {
        font-size: %s;
    }

    .pnx-tabulator {
        border: white solid 0.08rem !important;
    }
'''%(FONTSIZES['table_title'], FONTSIZES['table_txt'])

# CSS stylesheet for tabs
BASE_TABS_STYLE = '''
    .bk-tab {
        color:white;
    }
    
    .bk-tab.bk-active {
        font-weight: bold;
        color: %s !important;
        background-color: %s !important;
        border-color: white !important;
    }
'''%(CLRS['selected'], CLRS['secondary'])

ERRORED_TABS_STYLE = '''
    .bk-tab {
        font-weight: bold;
        font-size: 1rem;
        color:red;
    }
    
    .bk-tab.bk-active {
        font-weight: bold;
        font-size: 1rem;
        color: red !important;
        background-color: %s !important;
        border-color: red !important;
    }
'''%(CLRS['secondary'])

# Configuration for photometry and astrometry plots
PHOT_CONFIGS = {'toImageButtonOptions': {'filename': 'photometry', 'scale': 5}, 
                'displayModeBar': True, 'displaylogo': False,
                'modeBarButtonsToRemove': ['autoScale', 'lasso', 'select']}
AST_CONFIGS = {'toImageButtonOptions': {'filename': 'astrometry', 'scale': 5}, 
               'displayModeBar': True, 'displaylogo': False,
               'modeBarButtonsToRemove': ['autoScale', 'lasso', 'select']}

PHOT_FORMAT = ('<b>Time</b>: %{x:.3f}' +
            '<br><b>Mag.</b>: %{y:.3f}' +
            '<extra></extra>')
AST_FORMAT = ('<b>Time:</b> %{text:.3f}' + 
           '<br><span style="font-size:1rem">&#916;&#120572;</span><sup>*</sup>: %{x:.5f}' +
           '<br><span style="font-size:1rem">&#916;&#120575;</span>: %{y:.5f}' +
           '<extra></extra>') 