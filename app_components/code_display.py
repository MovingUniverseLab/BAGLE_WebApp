################################################
# Packages
################################################
import textwrap
import numpy as np

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import indicators, styles, traces
from app_components import paramztn_select, settings_tabs


################################################
# Dashboard - Code Panel
################################################
class CodePanel(Viewer):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)
    trace_info = param.ClassSelector(class_ = traces.AllTraceInfo)
    
    
    def __init__(self, **params):
        super().__init__(**params)

        # Variable to store 'Num_samps' slider watcher for wasy unwatching
        self.samps_watcher = None

        self.code_display = pn.widgets.CodeEditor(
            name = 'code_display',
            sizing_mode = 'stretch_both', 
            language = 'python',
            theme = styles.THEMES['code_theme'],
            styles = {'overflow':'visible'},
            disabled = True,
            readonly = True
        )

        self.code_layout = pn.FlexBox(
            self.code_display,
            sizing_mode = 'stretch_both',
            justify_content = 'center',
            align_content = 'center',
            styles = {'background': styles.CLRS['page_secondary'], 
                      'border': f'{styles.CLRS["page_border"]} solid 0.08rem'},
        )
        
        # Set dependencies
        self.settings_info.param_sliders['Num_pts'].param.watch(self._update_code_str, 'value')

        for error_bool in self.settings_info.errored_state.values():
            error_bool.param.watch(self.set_errored_layout, 'value')


    @pn.depends('paramztn_info.selected_paramztn', watch = True)
    def set_samps_dependency(self):
        # Unwatch first if exists
        if self.samps_watcher != None:
            self.settings_info.param_sliders['Num_samps'].param.unwatch(self.samps_watcher)
            self.samps_watcher = None

        if (self.paramztn_info.selected_paramztn != None) and ('GP' in self.paramztn_info.selected_paramztn):
            self.samps_watcher = self.settings_info.param_sliders['Num_samps'].param.watch(self._update_code_str, 'value')


    def set_errored_layout(self, *event):
        if event[0].obj.value == True:
            self.code_layout.objects = [indicators.get_indicator('error')]


    def reset_scroll(self):
        self.code_layout.clear()
        self.code_layout.objects = [self.code_display]


    def get_phot_code(self):
        phot_code = textwrap.dedent(
            ''' 

                ################################################
                # Photometry Data
                ################################################'''
        )

        phot_trace_keys = self.trace_info.main_phot_keys + self.trace_info.extra_phot_keys

        # We remove 'gp_prior' because the 'gp_predict' trace will already include the non-GP data information
        if 'gp_prior' in phot_trace_keys:
            phot_trace_keys.remove('gp_prior')

        for trace_key in phot_trace_keys:
            data_code = self.trace_info.all_traces[trace_key].get_data_code()
            phot_code += textwrap.dedent(data_code)

        return phot_code
    

    def get_ast_code(self):
        ast_trace_keys = self.trace_info.main_ast_keys + self.trace_info.extra_ast_keys

        if {'bs_res_unlen_pri', 'bs_res_unlen_pri'} <= set(ast_trace_keys):
            # remove the secondary source key to prevent having repeated data code
            ast_trace_keys.remove('bs_res_unlen_sec')

        if {'bs_res_len_pri', 'bs_res_len_sec'} <= set(ast_trace_keys):
            # remove the secondary source key to prevent having repeated data code
            ast_trace_keys.remove('bs_res_len_sec')

        ast_code = textwrap.dedent(
            ''' 

                ################################################
                # Astrometry Data
                ################################################'''
        )

        for trace_key in ast_trace_keys:
            data_code = self.trace_info.all_traces[trace_key].get_data_code()
            ast_code += textwrap.dedent(data_code)

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
                    import plotly.graph_objects as go
                    
                    from bagle import model
                    
                    # Note: celerite is only used for Gaussian Process
                    import celerite
                '''
                
                # Code to instantiate the BAGLE model
                mod_params_str = ''''''
                mod_param_values = self.settings_info.mod_param_values

                for i, key in enumerate(mod_param_values.keys()):
                    value = np.round(mod_param_values[key], 5)

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
                
                # Check if photometry is selected in dashboard
                if (len(self.trace_info.selected_phot_plots) != 0):
                    code_list.append(self.get_phot_code())

                # Check if astrometry is selected in dashboard
                if (len(self.trace_info.selected_ast_plots) != 0):
                    code_list.append(self.get_ast_code())

                py_code = ''
                for code in code_list:
                    py_code += textwrap.dedent(code)

                # Check if loading/error indicator is displayed
                if self.code_layout.objects[0].name != self.code_display.name:
                    self.code_layout.objects = [self.code_display]

                self.code_display.value = py_code


    def __panel__(self):
        return self.code_layout
