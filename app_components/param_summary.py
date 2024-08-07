# Packages
################################################
import numpy as np

from bagle import model

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import constants
from app_components import indicators, paramztn_select, settings_tabs


################################################
# Dashboard - Parameter Summary
################################################ 
class ParamSummary(Viewer):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)

    #######################
    # Panel Components
    #######################
    def __init__(self, **params):
        # Box for parameter summaries (model and derived)
        self.mod_pane = pn.pane.HTML(styles = {'color':'white', 'max-height':'min-content', 'padding':'0.5rem'})
        self.derived_pane = pn.pane.HTML(styles = {'color':'white', 'max-height':'min-content', 'padding':'0.5rem'})
        
        # Layout for summary pane
        self.summary_content = pn.FlexBox(
            self.mod_pane, 
            self.derived_pane, 
            styles = {'width':'max-content', 'height':'100%'})   
        
        self.summary_layout = pn.FlexBox(
            self.summary_content,
            justify_content = 'center',
            align_content = 'center',
            styles = {'border':'white solid 0.08rem', 
                      'background':constants.CLRS['secondary'],
                      'height':'100%',
                      'overflow':'scroll'}
        )
    
        super().__init__(**params)

    #######################
    # Methods
    #######################
    @pn.depends('settings_info.dashboard_checkbox.value', 'settings_info.trigger_param_change', watch = True)
    def update_summary(self):
        if (self.settings_info.lock_trigger == False) and ('summary' in self.settings_info.dashboard_checkbox.value):
            # Model parameter summary
            mod_html = ''''''
            for param in self.paramztn_info.selected_params:
                if constants.DEFAULT_RANGES[param][0] == None:
                    label = param
                else:
                    label = f'{param} [{constants.DEFAULT_RANGES[param][0]}]'
                
                if param in self.paramztn_info.selected_phot_params:
                    val = self.settings_info.mod_param_values[param][0]
                else:
                    val = self.settings_info.mod_param_values[param]
                
                mod_html += f'''
                    <span style="font-size:{constants.FONTSIZES['summary_txt']};">
                        <b>{label}</b>:  {round(val, 5)}
                    </span>'''
            mod_html = f'''
                <div style="display:flex; flex-direction:column; align-items:start;font-family:{constants.HTML_FONTFAMILY}">
                    <span style="font-size:{constants.FONTSIZES['header']}"><u><b>Model Parameters</b></u></span>
                    {mod_html}
                </div>           
            '''
            self.mod_pane.object = mod_html

            # Derived parameter summary 
            mod = getattr(model, self.paramztn_info.selected_paramztn)(**self.settings_info.mod_param_values)
            all_params_dict = vars(mod)
            
            derived_html = ''''''
            for param in all_params_dict.keys():
                if param not in self.paramztn_info.selected_params + ['raL', 'decL', 'use_gp_phot', 'root_tol']:
                    clr = 'white'
                    if constants.DEFAULT_RANGES[param][0] == None:
                        label = param
                    else:
                        label = f'{param} [{constants.DEFAULT_RANGES[param][0]}]'
                    
                    # Check if value type is a dictionary, np.ndarray, or float/integer
                    if isinstance(all_params_dict[param], dict):
                        val = round(all_params_dict[param][0], 5)
                        
                    elif isinstance(all_params_dict[param], np.ndarray):
                        # Check if np.ndarray is a vector
                        if len(all_params_dict[param]) > 1:
                            clr = 'rgb(166, 166, 166)'
                            round_arr = np.around(all_params_dict[param], 5)
                            val = np.array2string(round_arr, separator = ', ')
                        else:
                            val = round(all_params_dict[param][0], 5)
                    else:
                        val = round(all_params_dict[param], 5)
                    
                    derived_html += f'''
                        <span style="font-size:{constants.FONTSIZES['summary_txt']}">
                            <b style="color:{clr}">{label}</b>:  {val}
                        </span>
                    '''
                    
            derived_html = f'''
                <div style="display:flex;flex-direction:column;align-items:start;font-family:{constants.HTML_FONTFAMILY}">
                    <span style="font-size:{constants.FONTSIZES['header']}"><u><b>Derived Parameters</b></u></span>
                    {derived_html}
                </div>           
            '''     
            self.derived_pane.object = derived_html

            if 'indicator' in self.summary_layout.objects[0].name:
                self.summary_layout.objects = [self.summary_content]

    @pn.depends('settings_info.error_trigger', watch = True)
    def errored_layout(self):
        self.summary_layout.objects = [indicators.error]

    def __panel__(self):
        return self.summary_layout
    
