################################################
# Packages
################################################
import textwrap

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import constants
from app_components import indicators, paramztn_select, settings_tabs


################################################
# Dashboard - Code Panel
################################################
class CodePanel(Viewer):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)
    
    # Lists for the set of photometry plots and set of astrometry plots selected in plot checkbox
    selected_phot_plots, selected_ast_plots = param.List(), param.List()
    
    def __init__(self, **params):
        super().__init__(**params)
    
        # Variable to store 'Num_samps' slider watcher for wasy unwatching
        self.samps_watcher = None
        
        # Functions to get code strings for extra astrometry traces
        self.extra_ast_str_fns = {
            'ps_res_len': self.get_res_len_str,
            'bs_res_unlen': self.get_bs_res_unlen_str,
            'bs_res_len_pri': self.get_res_len_str,
            'bs_res_len_sec': self.get_res_len_str,
            'lens': self.get_lens_str
        }

        self.code_display = pn.widgets.CodeEditor(
            sizing_mode = 'stretch_both', 
            language = 'python',
            theme = 'tomorrow_night_eighties',
            styles = {'overflow':'visible'},
            disabled = True,
            readonly = True
        )

        self.code_layout = pn.FlexBox(
            objects = [self.code_display],
            sizing_mode = 'stretch_both',
            justify_content = 'center',
            align_content = 'center',
            styles = {'background':constants.CLRS['secondary'], 'border':'solid white 0.08rem'},
        )
        
        # Set dependencies
        self.settings_info.param_sliders['Num_pts'].param.watch(self._update_code_str, 'value')
    
    @pn.depends('paramztn_info.selected_paramztn', watch = True)
    def set_samps_dependency(self):
        # Unwatch if exists
        if self.samps_watcher != None:
            self.settings_info.param_sliders['Num_samps'].param.unwatch(self.samps_watcher)
            self.samps_watcher = None

        if (self.paramztn_info.selected_paramztn != None) and ('GP' in self.paramztn_info.selected_paramztn):
            self.samps_watcher = self.settings_info.param_sliders['Num_samps'].param.watch(self._update_code_str, 'value')

    @pn.depends('settings_info.error_trigger', watch = True)
    def set_errored_layout(self):
        self.code_layout.objects = [indicators.error]

    def get_phot_code(self):
        if 'GP' not in self.paramztn_info.selected_paramztn:
            phot_code = '''

                ################################################
                # Photometry Data
                ################################################
                # Non-GP Photometry
                phot = mod.get_photometry(t)
            '''
        else:
            selected_params = self.paramztn_info.selected_params
            
            # Get Matern-3/2 parameters
            log_sig = "mod_params['gp_log_sigma']"

            if 'gp_rho' in selected_params:
                log_rho = "np.log(mod_params['gp_rho'])"
            elif 'gp_log_rho' in selected_params:
                log_rho = "mod_params['gp_log_rho']"

            # DDSHO parameters
            log_Q = "np.log(2**-0.5)"
            log_omega0 = "mod_params['gp_log_omega0']"

            if 'gp_log_S0'in selected_params:
                log_S0 = "mod_params['gp_log_S0']"

            elif 'gp_log_omega04_S0' in selected_params:
                log_S0 = "mod_params['gp_log_omega04_S0'] - (4 * log_omega0)"

            elif 'gp_log_omega0_S0' in selected_params:
                log_S0 = "mod_params['gp_log_omega0_S0'] - log_omega0"
            
            num_samps = self.settings_info.param_sliders['Num_samps'].value
            
            phot_code = f'''

                ################################################
                # Photometry Data
                ################################################
                # Celerite Model
                cel_mod = model.Celerite_GP_Model(mod, 0)

                # Get Matern-3/2 GP Parameters
                    # Note: log = Natural Logarithm
                log_sig = {log_sig}
                log_rho = {log_rho}

                # Get DDSHO GP parameters
                    # Note: log = Natural Logarithm
                log_Q = {log_Q}
                log_omega0 = {log_omega0}
                log_S0 = {log_S0}

                # Make fake errors (mimicking OGLE photon noise)
                flux0 = 4000.0
                mag0 = 19.0
                mag_obs = cel_mod.get_value(t)

                flux_obs = flux0 * 10 ** ((mag_obs - mag0) / -2.5)
                flux_obs_err = flux_obs ** 0.5
                mag_obs_err = 1.087 / flux_obs_err

                # Make GP model
                m32 = celerite.terms.Matern32Term(log_sig, log_rho)
                sho = celerite.terms.SHOTerm(log_S0, log_Q, log_omega0)
                jitter = celerite.terms.JitterTerm(np.log(np.average(mag_obs_err)))
                kernel = m32 + sho + jitter

                gp = celerite.GP(kernel, mean = cel_mod, fit_mean = True)
                gp.compute(t, mag_obs_err)

                # Make fake photometry data for prior mean of GP
                mag_obs_corr = gp.sample(size = 1)[0]

                # GP Predictive Mean
                gp_pred_mean = gp.predict(mag_obs_corr, return_cov = False)

                # GP Prior Mean.  
                    # Note: mag_obs = mod.get_photometry(time) from a nonGP, PSPL model
                gp_prior_mean = mag_obs

                # GP Prior Samples
                    # shape is [GP sample, time]
                gp_samps = gp.sample(size = {num_samps})
            '''

        return phot_code
    
    def get_res_len_str(self):
        selected_paramztn = self.paramztn_info.selected_paramztn
        
        if 'PS' in selected_paramztn:
            if 'PL' in selected_paramztn:
                shape_str = '# For PSPL, shape is [image, time, RA/Dec]'
            elif 'BL' in selected_paramztn:
                shape_str = '# For PSBL, shape is [time, image, RA/Dec]'

        elif 'BS' in selected_paramztn:
            shape_str = '# For any binary-source model, shape is [time, source, image, RA/Dec]'

        ast_str = f'''
        # Resolved, Lensed Source Images
            {shape_str}
        res_len = mod.get_resolved_astrometry(t)
        '''

        return ast_str

    def get_bs_res_unlen_str(self):
        ast_str = '''
        # Resolved, Unlensed Sources
            # shape is [time, source, RA/Dec]
        res_unlen = mod.get_resolved_astrometry_unlensed(t)
        '''

        return ast_str

    def get_lens_str(self):
        selected_paramztn = self.paramztn_info.selected_paramztn
        
        if 'PL' in selected_paramztn:
            ast_str = '''
                # Point-Lens Astrometry
                    # shape is [time, RA/Dec]
                lens_ast = mod.get_lens_astrometry(t)
            '''
        elif 'BL' in selected_paramztn:
            ast_str = '''
                # Binary-lens Astrometry
                    # shape is [lens, time, RA/Dec]
                lens_ast = mod.get_resolved_lens_astrometry(t)
            '''

        return ast_str
    
    def get_ast_code(self):
        extra_ast = self.settings_info.ast_checkbox.value.copy()

        extra_ast_code = []
        if {'bs_res_len_pri', 'bs_res_len_sec'} <= set(extra_ast):
            # remove the secondary source key to prevent having repeated data
            extra_ast.remove('bs_res_len_sec')

        for key in extra_ast:
            extra_ast_code.append(self.extra_ast_str_fns[key]())

        main_ast_code = f'''

            ################################################
            # Astrometry Data
            ################################################
            # Unresolved, Lensed Source(s)
                # shape is [time, RA/Dec]
            unres_len = mod.get_astrometry(t)

            # Unresolved, Unlensed Source(s)
                # shape is [time, RA/Dec]
            unres_unlen = mod.get_astrometry_unlensed(t)
        '''

        ast_code = ''
        for code_str in [main_ast_code] + extra_ast_code:
            ast_code += textwrap.dedent(code_str)

        return ast_code
    
    @pn.depends('settings_info.trigger_param_change', 'settings_info.dashboard_checkbox.value',
                'settings_info.phot_checkbox.value', 'settings_info.ast_checkbox.value', watch = True)
    def _update_code_str(self, *event):
        # Check if code panel is displayed.
        # Check if lock is on.
        if 'code' in self.settings_info.dashboard_checkbox.value:
            if self.settings_info.lock_trigger == False:
                # Code to import packages
                package_code = '''
                    ################################################
                    # Packages
                    ################################################
                    import numpy as np
                    from BAGLE_Microlensing.src.bagle import model

                    # Note: celerite is only used for Gaussian Process
                    import celerite
                '''
                
                # Code to instantiate the BAGLE model
                mod_params_str = ''''''
                mod_param_values = self.settings_info.mod_param_values

                for i, key in enumerate(mod_param_values.keys()):
                    value = mod_param_values[key]

                    if i != len(mod_param_values.keys()) - 1:
                        comma = ','
                    else:
                        comma = ''

                    if key in self.paramztn_info.selected_phot_params:
                        key_value = f''''{key}': np.array({value}){comma}
                        '''
                    else:
                        key_value = f''''{key}': {value}{comma}
                        '''
                    mod_params_str += key_value


                min_t = self.settings_info.param_sliders['Time'].start
                max_t = self.settings_info.param_sliders['Time'].end
                num_pts = self.settings_info.param_sliders['Num_pts'].value

                mod_time_code = f'''

                    ################################################
                    # Model and Time
                    ################################################
                    paramztn_str = '{self.paramztn_info.selected_paramztn}'
                    mod_params = {{
                        {mod_params_str}}}  

                    # Instantiate BAGLE model
                    mod = getattr(model, paramztn_str)(**mod_params)

                    # Time points
                    t = np.linspace({min_t}, {max_t}, {num_pts})
                '''

                code_list = [package_code, mod_time_code]

                # Code to get data from model
                selected_phot_plots = list(set(constants.PHOT_PLOT_NAMES) & set(self.settings_info.dashboard_checkbox.value))
                selected_ast_plots = list(set(constants.AST_PLOT_NAMES) & set(self.settings_info.dashboard_checkbox.value))
                
                # Check if photometry is selected in dashboard
                if (len(selected_phot_plots) != 0):
                    code_list.append(self.get_phot_code())

                # Check if astrometry is selected in dashboard
                if (len(selected_ast_plots) != 0):
                    code_list.append(self.get_ast_code())

                py_code = ''
                for code in code_list:
                    py_code += textwrap.dedent(code)

                # Check if loading/error indicator is displayed
                if 'indicator' in self.code_layout.objects[0].name:
                    self.code_layout.objects = [self.code_display]

                self.code_display.value = py_code

    def __panel__(self):
        return self.code_layout
