################################################
# Packages
################################################
import re
from functools import partial
from itertools import cycle

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from bagle import model, model_fitter
import celerite

import panel as pn
from panel.viewable import Viewer
from panel.theme import Material
from bokeh.models import Tooltip
from bokeh.models.dom import HTML
import param


################################################
# Initial BAGLE Configs
################################################
# List of model parameterizations
ALL_MODS = [
    'PSPL_Phot_noPar_Param1', 'PSPL_Phot_noPar_Param2', 
    'PSPL_Phot_Par_Param1', 'PSPL_Phot_Par_Param2',
    'PSPL_Astrom_Par_Param3', 'PSPL_Astrom_Par_Param4',
    'PSPL_PhotAstrom_noPar_Param1', 'PSPL_PhotAstrom_noPar_Param2', 'PSPL_PhotAstrom_noPar_Param3', 'PSPL_PhotAstrom_noPar_Param4',
    'PSPL_PhotAstrom_Par_Param1', 'PSPL_PhotAstrom_Par_Param2', 'PSPL_PhotAstrom_Par_Param3', 'PSPL_PhotAstrom_Par_Param4',
    'PSPL_Phot_Par_GP_Param1', 'PSPL_Phot_Par_GP_Param2',
    'PSPL_Phot_Par_GP_Param2_2', 'PSPL_Phot_Par_GP_Param2_3',
    'PSPL_PhotAstrom_Par_GP_Param1', 'PSPL_PhotAstrom_Par_GP_Param2', 'PSPL_PhotAstrom_Par_GP_Param3', 'PSPL_PhotAstrom_Par_GP_Param4',
    'PSPL_PhotAstrom_Par_GP_Param3_1'
]

# Dictionary for default slider ranges of model parameters
    # Note: the list order is [Units, Default, Min, Max, Step]
DEFAULT_RANGES = {
    'Time': ['MJD', 56500.0, 54500.0, 56500.0, 0.1],
    'mL': ['Msun', 10.0, 0.0, 100.0, 0.1],
    't0': ['MJD', 55500, 55000, 56000, 0.1],
    't0_prim': [None, None, None, None, 0.1],
    'xS0': ['arcsec', None, None, None, 0.1],
    'xS0_E': ['arcsec', 0.0, -5.0, 5.0, 0.1],
    'xS0_N': ['arcsec', 0.0, -5.0, 5.0, 0.1],
    'xL0': ['lens pos', None, None, None, 0.1],
    'u0': ['Einstein units', None, None, None, 0.1],
    'u0_amp': ['Einstein units', 0.5, -1.0, 1.0, 0.1],
    'u0_hat': [None, None, None, None, 0.1],
    'u0_amp_prim': ['Einstein units', 0.0, -1.0, 1.0, 0.1],
    'thetaS0': ['mas', None, None, None, 0.1],
    'beta': ['mas', 0.0, -2.0, 2.0, 0.01],
    'muL': ['mas/yr', None, None, None, 0.1],
    'muL_E': ['mas/yr', 0.0, -20.0, 20.0, 0.1],
    'muL_N': ['mas/yr', 0.0, -20.0, 20.0, 0.1],
    'muS': ['mas/yr', None, None, None, 0.1],
    'muS_E': ['mas/yr', 2.0, -15.0, 15.0, 0.1],
    'muS_N': ['mas/yr', 0.0, -15.0, 15.0, 0.1],
    'muRel': ['mas/yr', None, None, None, 0.1],
    'muRel_E': ['mas/yr', None, None, None, 0.1],
    'muRel_N': ['mas/yr', None, None, None, 0.1],
    'muRel_amp': ['mas/yr', None, None, None, 0.1],
    'muRel_hat': [None, None, None, None, 0.1],
    'kappa': ['mas/Msun', None, None, None, 0.1],
    'dL': ['pc', 3500.0, 1000.0, 8000.0, 0.1],
    'dS': ['pc', 5000.0, 100.0, 10000.0, 0.1],
    'dL_dS': [None, 0.5, 0.01, 0.99, 0.1],
    'b_sff': [None, 0.75, 0.0, 1.5, 0.1],
    'mag_src': ['mag', 19.0, 14.0, 24.0, 0.1],
    'mag_src_pri': ['mag', 19.0, 14.0, 24.0, 0.1],
    'mag_src_sec': ['mag', 19.0, 14.0, 24.0, 0.1],
    'mag_base': ['mag', 19.0, 14.0, 24.0, 0.1],
    'tE': ['days', 200.0, 1.0, 400.0, 0.1],
    'piE': ['Einstein units', None, None, None, 0.1],
    'piE_amp': ['Einstein units', None, None, None, 0.1],
    'piE_E': ['Einstein units', 0.05, -1.0, 1.0, 0.01],
    'piE_N': ['Einstein units', 0.05, -1.0, 1.0, 0.01],
    'piRel': ['Einstein units', None, None, None, 0.1],
    'piEN_piEE': [None, 0.0, -10.0, 10.0, 0.1],
    'thetaE': ['mas', 2.0, 0.0, 10.0, 0.1],
    'thetaE_amp': ['mas', None, None, None, 0.1],
    'thetaE_E': ['mas', None, None, None, 0.1],
    'thetaE_N': ['mas', None, None, None, 0.1],
    'thetaE_hat': [None, None, None, None, 0.1],
    'log10_thetaE': ['mas', 0.5, -1, 1, 0.1],
    'piS': ['mas', 0.12, 0.01, 1.0, 0.1],
    'piL': ['mas', 0.12, 0.01, 1.0, 0.1],
    'raL': ['deg', 50, 0, 360, 0.1],
    'decL': ['deg', 30, -90, 90, 0.1],
    'gp_log_sigma': [None, -4, -10, 10, 0.1],
    'gp_log_rho': ['log(days)', 1.3, -2, 2, 0.1],
    'gp_rho': ['days', 20, 0.01, 100, -0.1],
    'gp_log_omega0': ['log(1/days)', 1, -10, 10, 0.1],
    'gp_log_S0': [None, -7, -15, 5, 0.1],
    'gp_log_omega04_S0': [None, -7, -15, 5, 0.1],
    'gp_log_omega0_S0': [None, -7, -15, 5, 0.1]
}


################################################
# Initial Panel Configs
################################################
pn.extension('tabulator', 'plotly', design = 'bootstrap')
pn.config.theme = 'dark'

# Page colors
GP_ALPHA = 0.7
CLRS = {
    'main': '#121212',
    'secondary': '#2B3035',
    'light': '#4BFFEF',
    'selected': '#65AFE9',
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
SLIDER_STYLE = '''
    :host {
        --design-primary-color: %s;
        --design-secondary-color: %s;
    }
    
    .bk-slider-title {
        font-size: %s;
    }
'''%(CLRS['light'], CLRS['main'], FONTSIZES['slider'])

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

PHOT_TXT = ('<b>Time</b>: %{x:.3f}' +
            '<br><b>Mag.</b>: %{y:.3f}' +
            '<extra></extra>')
AST_TXT = ('<b>Time:</b> %{text:.3f}' + 
           '<br><span style="font-size:1rem">&#916;&#120572;</span><sup>*</sup>: %{x:.5f}' +
           '<br><span style="font-size:1rem">&#916;&#120575;</span>: %{y:.5f}' +
           '<extra></extra>') 


################################################
# Model Selection Section
################################################
class ModSelect(Viewer):
    # Model header
    mod_header = pn.widgets.StaticText(value = 'Model:',
                                       styles = {'font-size': FONTSIZES['header'], 
                                                 'font-weight':'550', 
                                                 'margin-right':'0.9rem'})

    # Model selection boxes
    srclens_type = pn.widgets.Select(name = '', 
                                     options = {'Point-Source Point-Lens': 'PSPL'}, 
                                     align = 'center', sizing_mode = 'scale_width', 
                                     stylesheets = [DROPDOWN_STYLE])

    data_type = pn.widgets.Select(name = '', 
                                  options = {'Photometry': 'Phot', 
                                             'Astrometry': 'Astrom', 
                                             'Photometry-Astrometry': 'PhotAstrom'}, 
                                  align = 'center', sizing_mode = 'scale_width', 
                                  stylesheets = [DROPDOWN_STYLE])

    par_type = pn.widgets.Select(name = '', 
                                 options = {'No Parallax': 'noPar', 
                                            'Parallax': 'Par'}, 
                                 align = 'center', sizing_mode = 'scale_width', 
                                 stylesheets = [DROPDOWN_STYLE])

    gp_type = pn.widgets.Select(name = '', 
                                options = {'No Gaussian Process': '', 
                                            'Gaussian Process': 'GP'}, 
                                align = 'center', sizing_mode = 'scale_width', 
                                stylesheets = [DROPDOWN_STYLE])
    
    type_dict = param.Dict(default = {})
    
    def __init__(self, **params):
        super().__init__(**params)
        objs = [self.srclens_type, self.data_type, self.par_type, self.gp_type]
        insert_idx = np.arange(1, 2 * len(objs) - 2, 2)
        
        for i in insert_idx:
            plus = pn.widgets.StaticText(name = '', value = '+', align = 'center',
                                         styles = {'font-size':FONTSIZES['plus']})
            objs = np.insert(objs, i, plus)
        
        # Layout of model selection row
        self.mod_layout = pn.Row(objects = [self.mod_header] + list(objs),
                                 styles = {'padding-left':'10%',
                                           'padding-right':'10%',
                                           'margin-bottom':'0.5rem'})
        
    @pn.depends('srclens_type.value', 'data_type.value', 
                'par_type.value', 'gp_type.value', watch = True, on_init = True)
    def _update_types(self):
        self.type_dict = {
            'srclens': self.srclens_type.value, 
            'data': self.data_type.value, 
            'par': self.par_type.value, 
            'gp': self.gp_type.value
        }
    
    def __panel__(self):
        return self.mod_layout
    

################################################
# Parameterization Selection Section
################################################
class ParamztnSelect(Viewer):
    # To be instantiated ModSelect class
    mod_info = param.ClassSelector(class_ = ModSelect)
    
    # Current selected paramertization and parameters
    selected_paramztn = param.String(allow_None = True)
    selected_params = param.List()
    
    # Dictionary to store buttons
    paramztn_btns = param.Dict(default = {})
    
    # Flex box to display buttons
    paramztn_box = pn.FlexBox(align = 'center')

    # Parameterization Header
    paramztn_header = pn.widgets.StaticText(value = f'Parameterization:', align = 'start',
                                            styles = {'font-size':FONTSIZES['header'],
                                                      'font-weight':'550', 
                                                      'margin-right':'1rem'})
    # Error message in case of no parameterizations
    paramztn_error = pn.widgets.StaticText(
        value = 'ERROR: There are currently no supported parameterizations for this model. Please try a different selection.',
        styles = {'font-size':FONTSIZES['paramztn_error'], 
                  'text-align':'center',
                  'font-weight':'550', 
                  'margin-bottom':'-0.2rem'},
        stylesheets = ['''.bk-clearfix {color: red;}''']
    )
    
    # Layout of parameterization selection row
    paramztn_layout = pn.Row(styles = {'padding-right':'5%', 
                                       'padding-left':'5%',
                                       'margin-bottom':'-0.3rem'})
        
    @pn.depends('mod_info.type_dict', watch = True, on_init = True)
    def _update_paramztn(self):
        '''
        Updates the contents of the parameterization selection row of the page.
        '''  
        mod_types = self.mod_info.type_dict
        
        # Clear selected parameterization
        self.selected_paramztn = None
        
        # Get paramaterizations for selected model
        if mod_types['gp'] == 'GP':
            mod_regex = '_'.join(list(mod_types.values())) + '_Param'
        else:
            mod_regex = '_'.join([mod_types[key] for key in mod_types.keys() 
                                  if key != 'gp']) + '_Param'

        mod_paramztns = [mod for mod in ALL_MODS if re.match(mod_regex, mod)]
        
        # No parameterizations found for selected model
        if len(mod_paramztns) == 0: 
            self.paramztn_layout.objects = [pn.HSpacer(), self.paramztn_error, pn.HSpacer()]
            
        # At least one parameterization found for selected model
        else:
            for paramztn in mod_paramztns:
                # Update paramztn_btns dictionary
                if paramztn not in self.paramztn_btns.keys():
                    # Write HTML for button tooltip
                    all_param_names = self.get_param_names(paramztn, mod_types)
                
                    tooltip_html = ''''''
                    for param in all_param_names:
                        tooltip_html += f'''<span>{param}</span>'''

                    tooltip_html = HTML(f'''
                        <div style = "display:flex; align-items:center; flex-direction:column; 
                                      padding:0.25rem; border:0.04rem black solid; color:#121212;
                                      font-size:{FONTSIZES['tooltip']}; font-weight:bold;">
                            {tooltip_html}
                        </div>
                    ''')
                
                    # Create parameterization Buttons
                    self.paramztn_btns[paramztn] = pn.widgets.Button(name = paramztn, button_type = 'primary', 
                                                                     description = (Tooltip(content = tooltip_html, 
                                                                                            position = 'bottom')),
                                                                     stylesheets = [BASE_BTN_STYLE])
                else:
                    self.paramztn_btns[paramztn].stylesheets = [BASE_BTN_STYLE]
                self.paramztn_btns[paramztn].on_click(partial(self.change_selected_btn, 
                                                              mod_types = mod_types))
    
            # Get relevant buttons and update paramztn_box
            self.paramztn_box.objects = [self.paramztn_btns[key] for key in mod_paramztns]
            self.paramztn_layout.objects = [self.paramztn_header, self.paramztn_box]
    
            
    def get_param_names(self, paramztn, mod_types):
        '''
        Gets parameter names for a given parameterization.
        '''

        class_num = re.search('Param.*', paramztn).group()
        if mod_types['gp'] == 'GP':
            param_class_str = '_'.join([mod_types['srclens'], mod_types['gp'], mod_types['data'] + class_num])
        else:
            param_class_str = '_'.join([mod_types['srclens'], mod_types['data'] + class_num])

        param_class = getattr(model, param_class_str)
        all_param_names = (param_class.fitter_param_names + param_class.phot_param_names + 
                           param_class.phot_optional_param_names + param_class.ast_optional_param_names)

        if mod_types['par'] == 'Par':
            all_param_names += ['raL', 'decL']

        return all_param_names
    
    def change_selected_btn(self, event, mod_types): 
        '''
        Changes the CSS of parameterization buttons and the relevent selected parameters.
        '''
        
        if (event.obj.name != self.selected_paramztn):
            # Reset CSS of old selected button if it exists
            if self.selected_paramztn != None:
                self.paramztn_btns[self.selected_paramztn].stylesheets = [BASE_BTN_STYLE]
            
            # Change CSS of new selected button
            event.obj.stylesheets = [SELECTED_BTN_STYLE]

            # Update selected parameters
            self.selected_paramztn = event.obj.name
            self.selected_params = self.get_param_names(event.obj.name, mod_types)
            
    def __panel__(self):
        return self.paramztn_layout
    

################################################
# Dashboard - Parameter Tabs
################################################
class ParamTabs(Viewer):
    # To be instantiated ParamztnSelect class
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    
    # Parameters to prevent unwanted updates or trigger updates
    lock_trigger = param.Boolean()
    trigger_param_change = param.Boolean()
    
    # Parameter to check for errors
    error_msg = pn.pane.HTML(object = None, name = 'ERRORED SLIDERS')
    
    # Dictionary for parameter values
    param_values = param.Dict(default = {})
    
    # Dictionary to store all sliders and watchers. 
    # Note: This is needed so that we don't always create new sliders and lag the page from memory leaks.
    param_sliders = param.Dict(default = {})
    slider_watchers = param.Dict(default = {})
    
    # Layout for model parameter-related sliders
    mod_sliders = pn.FlexBox(flex_wrap = 'wrap')
    
    # Table for range settings
    range_table = pn.widgets.Tabulator(name = 'Slider Settings',
                                       text_align = 'left', layout = 'fit_columns',
                                       editors = {'Units': None}, 
                                       sizing_mode = 'stretch_both',
                                       stylesheets = [TABLTR_STYLE])
    
    # Checkboxes for dashboard/plot settings
    dashboard_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{FONTSIZES['header']}"><u><b>Dashboard Layout</b></u></span>''',
        styles = {'color':'white', 'max-height':'min-content'}
    )
    dashboard_checkbox = pn.widgets.CheckBoxGroup(inline = False)
    dashboard_settings = pn.Column(dashboard_settings_header, 
                                   dashboard_checkbox, 
                                   styles = {'margin':'0.5rem'})
    
    plot_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{FONTSIZES['header']}"><u><b>Plot Settings</b></u></span>''',
        styles = {'color':'white', 'max-height':'min-content'}
    )
    plot_checkbox = pn.widgets.CheckBoxGroup(inline = False)
    plot_settings = pn.Column(plot_settings_header, 
                              plot_checkbox, 
                              styles = {'margin':'0.5rem'})
    # Layout for settings tab
    settings_layout = pn.FlexBox(dashboard_settings, 
                                 plot_settings, 
                                 name = 'Other Settings',
                                 justify_content = 'center',
                                 styles = {'overflow':'scroll'})
    
    def __init__(self, **params):
        super().__init__(**params)
        # Time and number slider
        self.param_sliders['Time'] = pn.widgets.FloatSlider(name = 'Time [MJD]',
                                                            format = '1[.]000',
                                                            margin = (10, 0, -2, 10),
                                                            design = Material,
                                                            stylesheets = [SLIDER_STYLE])
        
        self.param_sliders['Num'] = pn.widgets.IntSlider(name = 'Number of GP Samples',
                                                           start = 0, value = 3, end = 10,
                                                           visible = False,
                                                           format = '1[.]000',
                                                           margin = (10, 0, -2, 10),
                                                           design = Material,
                                                           stylesheets = [SLIDER_STYLE])
        
        # Layout for sliders
        self.sliders_layout = pn.Column(self.param_sliders['Time'],
                                        self.param_sliders['Num'],
                                        pn.layout.Divider(),
                                        self.mod_sliders,
                                        name = 'Parameter Sliders',
                                        styles = {'overflow':'scroll', 'height':'100%'})
        
        # Layout for entire tab section
        self.tabs_layout = pn.Tabs(styles = {'border':'white solid 0.08rem',
                                             'background':CLRS['secondary'],
                                             'margin':'0.2rem', 'margin-bottom':'0.1rem'})
    
    @pn.depends('paramztn_info.selected_params', watch = True)
    def _update_table_and_checks(self):
        paramztn = self.paramztn_info.selected_paramztn
        
        # Update checkboxes
        if '_PhotAstrom_' in paramztn:
            db_options = ['Photometry', 'Astrometry', 'Parameter Summary']
            plot_options = ['Show Time Markers', 'Show Full Traces', 'Show Resolved Images']
        elif '_Astrom_' in paramztn:
            db_options = ['Astrometry', 'Parameter Summary']
            plot_options = ['Show Time Markers', 'Show Full Traces', 'Show Resolved Images']
        elif '_Phot_' in paramztn:
            db_options = ['Photometry', 'Parameter Summary']
            plot_options = ['Show Time Markers', 'Show Full Traces']
        
        # Lock used to not trigger checkbox-related changes
            # This is needed because same changes will trigger through data frame update
        self.lock_trigger = True
        self.dashboard_checkbox.param.update(options = db_options, value = db_options)  
        self.plot_checkbox.param.update(options = plot_options, value = ['Show Time Markers', 'Show Full Traces'])
        self.lock_trigger = False
        
        # Update range data frame
        idx_list = ['Time'] + self.paramztn_info.selected_params
        range_df = pd.DataFrame.from_dict(DEFAULT_RANGES, orient = 'index').loc[idx_list]
        range_df.columns = ['Units', 'Default', 'Min', 'Max', 'Step']
        range_df.index.name = 'Parameter'
        
        self.range_table.value = range_df
        
        # Reset tab to start
        self.tabs_layout.active = 0
        
    @pn.depends('range_table.value', watch = True)
    def _update_sliders(self):
        df = self.range_table.value
        for param in df.index:
            units = df.loc[param].iloc[0]
            default_val = df.loc[param].iloc[1]   
            min_val = df.loc[param].iloc[2]
            max_val = df.loc[param].iloc[3]
            step_val = df.loc[param].iloc[4]
            
            error_html = ''''''
            if np.any(np.isnan([default_val, min_val, max_val, step_val])):
                error_html += '''<li>Range inputs must be a number.</li>'''     
            if (min_val >= max_val):
                error_html += '''<li>The minimum value must be smaller than the maximum value</li>'''
            if ((default_val < min_val) or (default_val > max_val)):
                error_html += '''<li>The default value is not inside the range</li>'''
            if (step_val > (abs(max_val - min_val))):
                error_html += '''<li>The step size cannot be larger than the range size</li>'''           
             
            # There exists an error
            if error_html != '''''':
                error_param = f'''<span style="color:#ff9999";>{param}</span>'''
                self.error_msg.object = f'''
                    <span style="color:red; font-size:{FONTSIZES['error_title']};"">Errors in {error_param} Slider:</span>
                    <ul style="color:white; font-size:{FONTSIZES['error_txt']};">{error_html}</ul>
                '''
                self.tabs_layout.objects = [self.error_msg, self.range_table]
                self.tabs_layout.stylesheets = [ERRORED_TABS_STYLE]
                return
            
            # No error and is a model parameter
            elif param != 'Time':  
                # Create new slider if doesn't exist
                if param not in self.param_sliders:
                    if units == None:
                        param_label = param
                    else:
                        param_label = param + f' [{units}]' 

                    self.param_sliders[param] = pn.widgets.FloatSlider(name = param_label,
                                                                       value = default_val, 
                                                                       start = min_val, 
                                                                       end = max_val, 
                                                                       step = step_val,
                                                                       format = '1[.]000',
                                                                       margin = (10, 10, 10, 10),
                                                                       design = Material,
                                                                       stylesheets = [SLIDER_STYLE]) 
                    
                # Update slider if exists
                else:
                    # Unwatch before updating to prevent multiple repeated watchers (i.e. memory leak)
                    self.param_sliders[param].param.unwatch(self.slider_watchers[param])
                    self.param_sliders[param].param.update(value = default_val, 
                                                           start = min_val, 
                                                           end = max_val,
                                                           step = step_val)
            
                # Make watcher for slider
                self.slider_watchers[param] = self.param_sliders[param].param.watch(self.update_param_values, 'value')
            
            # Change Time slider
            else:
                self.lock_trigger = True
                self.param_sliders[param].param.update(value = default_val, 
                                                       start = min_val, 
                                                       end = max_val,
                                                       step = step_val)                
                self.lock_trigger = False
                
        # Get relevant sliders and update slider_box
        self.mod_sliders.objects = [self.param_sliders[key] for key in self.paramztn_info.selected_params]
        
        # Reveal number sample slider
        if 'GP' in self.paramztn_info.selected_paramztn:
            self.param_sliders['Num'].visible = True
        else:
            self.param_sliders['Num'].visible = False
        
        # Initialize param values
        self.update_param_values()
        
        # Change slider tab back to sliders if no errors        
        self.tabs_layout.objects = [self.sliders_layout, self.range_table, self.settings_layout]
        self.tabs_layout.stylesheets = [BASE_TABS_STYLE]
        
        self.error_msg.object = None
        
    def update_param_values(self, *events):
        '''
        Update the dictionary for parameter values based on slider inputs.
        Note that the '*events' argument is only used to set the dependency on the sliders.
        '''
        # Update model parameter values
        self.param_values = {key: self.param_sliders[key].value for key in self.paramztn_info.selected_params}
        
        # Note: this is needed because if self.param_values doesn't change, updates don't occur
            # An example of this is changing slider limits, but not the slider value
        self.trigger_param_change = not self.trigger_param_change
        
    def __panel__(self):
        return self.tabs_layout


################################################
# Dashboard - Parameter Summary
################################################ 
class ParamSummary(Viewer):
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    param_info = param.ClassSelector(class_ = ParamTabs)
    
    # Box for parameter summaries (model and derived)
    mod_pane = pn.pane.HTML(styles = {'color':'white', 'max-height':'min-content', 'padding':'0.5rem'})
    derived_pane = pn.pane.HTML(styles = {'color':'white', 'max-height':'min-content', 'padding':'0.5rem'})
    
    summary_layout = pn.FlexBox(mod_pane, 
                                derived_pane, 
                                justify_content = 'center',
                                sizing_mode = 'stretch_both',
                                styles = {'border':'white solid 0.08rem', 
                                          'overflow':'scroll',
                                          'background':CLRS['secondary'],
                                          'margin':'0.2rem', 'margin-bottom':'0.1rem'})   
    
    @pn.depends('param_info.trigger_param_change', watch = True)
    def update_summary(self):
        if (self.param_info.lock_trigger == False) and (self.summary_layout.visible == True):
                        
            # Model parameter summary
            mod_html = ''''''
            for key in self.param_info.param_values.keys():
                if DEFAULT_RANGES[key][0] == None:
                    label = key
                else:
                    label = f'{key} [{DEFAULT_RANGES[key][0]}]'
                    
                mod_html += f'''<span><b>{label}</b>:  {round(self.param_info.param_values[key], 5)}</span><br>'''
            mod_html = f'''
                <div style="display:flex; flex-direction:column; align-items:center;">
                    <span style="font-size:{FONTSIZES['header']}"><u><b>Model Parameters</b></u></span>
                    <div style="font-size:{FONTSIZES['summary_txt']}">
                        {mod_html}
                    </div>
                </div>           
            '''
            self.mod_pane.object = mod_html

            # Derived parameter summary 
            mod = getattr(model, self.paramztn_info.selected_paramztn)(**self.param_info.param_values)
            all_params_dict = vars(mod)

            derived_html = ''''''
            for key in all_params_dict.keys():
                if key not in self.paramztn_info.selected_params + ['raL', 'decL', 'use_gp_phot']:
                    clr = 'white'
                    if DEFAULT_RANGES[key][0] == None:
                        label = key
                    else:
                        label = f'{key} [{DEFAULT_RANGES[key][0]}]'
                    
                    if type(all_params_dict[key]) == dict:
                        val = round(all_params_dict[key][0], 5)
                    elif type(all_params_dict[key]) == np.ndarray:
                        if len(all_params_dict[key]) == 1:
                            val = round(all_params_dict[key][0], 5)
                        else:
                            clr = '#a6a6a6'
                            round_arr = np.around(all_params_dict[key], 5)
                            val = np.array2string(round_arr, separator = ', ')
                    else:
                        val = round(all_params_dict[key], 5)
                    
                    derived_html += f'''<span><b style="color:{clr};">{label}</b>:  {val}</span><br>'''
                    
            derived_html = f'''
                <div style="display:flex;flex-direction:column;justify-content:center;">
                    <span style="font-size:{FONTSIZES['header']}"><u><b>Derived Parameters</b></u></span>
                    <div style="font-size:{FONTSIZES['summary_txt']}">
                        {derived_html}
                    </div>
                </div>           
            '''     
            self.derived_pane.object = derived_html
         
    def __panel__(self):
        return self.summary_layout

    
################################################
# Dashboard - Plots
################################################
class Trace:   
    def __init__(self, legend_group, show_legend, primary_clr, secondary_clr, sizing, hover_format, dash = 'dash'):
        '''
        sizing: a list for trace/marker sizes ([time, full, marker])
        '''
        self.legend_group, self.show_legend = legend_group, show_legend
        self.primary_clr, self.secondary_clr = primary_clr, secondary_clr,
        self.sizing = sizing
        self.hover_format = hover_format
        self.dash = dash
    
    def time_trace(self, x_data, y_data, time_idx, zorder, text = None):
        return go.Scatter(x = x_data[time_idx], y = y_data[time_idx], 
                          name = '', zorder = zorder,
                          legendgroup = self.legend_group,
                          legendgrouptitle = dict(text = self.legend_group, font_size = FONTSIZES['legendgroup']),
                          line = dict(color = self.primary_clr, width = self.sizing[0]),
                          text = text, hovertemplate = self.hover_format, showlegend = self.show_legend)
    
    def full_trace(self, x_data, y_data, text = None):
        return go.Scatter(x = x_data, y = y_data,
                          legendgroup = self.legend_group, zorder = -1,
                          line = dict(color = self.secondary_clr, width = self.sizing[1], dash = self.dash),
                          text = text, hovertemplate = self.hover_format, showlegend = False)
    
    def time_marker(self, x_data, y_data, marker_idx, zorder):
        return go.Scatter(x = [x_data[marker_idx]], y = [y_data[marker_idx]],
                          zorder = zorder,
                          legendgroup = self.legend_group,
                          mode = 'markers', marker = dict(color = self.primary_clr, size = self.sizing[2]),
                          hoverinfo = 'skip', showlegend = False) 

class PlotRow(Viewer):
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    param_info = param.ClassSelector(class_ = ParamTabs)

    def __init__(self, **params):
        super().__init__(**params)
        self.phot_main_data, self.ast_main_data = {}, {}
        self.gp_samps = None, 
        self.time = []
        
        self.phot_traces = {
            'phot': Trace('Photometry', False, 'red', 'rgb(255, 77, 77)', 
                          [2, 1.5, 10], PHOT_TXT),
            'gp_predict_mean': Trace('Predictive Mean', True, 'red', f'rgba(255, 77, 77, 0.8)', 
                                     [1.4, 0.9, 10], PHOT_TXT, dash = 'solid'),
            'gp_prior_mean': Trace('Prior Mean', True, 'orange', 'rgba(255, 193, 77, 0.8)', 
                                   [1.4, 0.9, 10], PHOT_TXT, dash = 'solid')  
        } 
        
        self.ast_traces = {
            'lensed_pspl': Trace('Unresolved, Lensed Source', True, 'red', 'rgb(255, 77, 77)', 
                                 [2, 1.5, 10], AST_TXT),
            'unlensed_pspl': Trace('Unresolved, Unlensed Source', True, 'orange', 'rgb(255, 193, 77)', 
                                   [2, 1.5, 10], AST_TXT),
            'resolved_pspl_1': Trace('Resolved, Lensed Source Images', True, 'yellow', 'rgb(255, 255, 77)', 
                                     [1.2, 0.6, 6], AST_TXT),
            'resolved_pspl_2': Trace('Resolved, Lensed Source Images', False, 'yellow', 'rgb(255, 255, 77)', 
                                     [1.2, 0.6, 6], AST_TXT) 
        }
        
        # This is an initial figure for stylistic purposes (not really necessary)
        init_fig = go.Figure(layout = dict(plot_bgcolor = CLRS['secondary'], paper_bgcolor = CLRS['secondary']))
        init_fig.update_xaxes(showgrid = False, zeroline = False, showticklabels = False)
        init_fig.update_yaxes(showgrid = False, zeroline = False, showticklabels = False)
        
        self.phot_pane = pn.pane.Plotly(object = init_fig,
                                        config = PHOT_CONFIGS,
                                        sizing_mode = 'stretch_both',
                                        visible = False,
                                        styles = {'border':'white solid 0.08rem', 
                                                  'background':CLRS['secondary'],
                                                  'margin':'0.2rem',
                                                  'padding':'0.5rem', 'padding-right':'0'})

        self.ast_pane = pn.pane.Plotly(object = init_fig,
                                       config = AST_CONFIGS,
                                       sizing_mode = 'stretch_both',
                                       visible = False,
                                       styles = {'border':'white solid 0.08rem', 
                                                 'background':CLRS['secondary'],
                                                 'margin':'0.2rem',
                                                 'padding':'0.5rem', 'padding-right':'0'})

        self.plot_layout = pn.Row(self.phot_pane, self.ast_pane, styles = {'height':'65%'})
    
        self.param_info.param_sliders['Time'].param.watch(self._update_plots, 'value')
        self.param_info.param_sliders['Num'].param.watch(self.update_traces, 'value')

    @pn.depends('param_info.trigger_param_change', 'param_info.plot_checkbox.value', watch = True)
    def update_traces(self, *events):
        if (self.param_info.lock_trigger == False) and (self.plot_layout.visible == True):
            
            t = np.linspace(self.param_info.param_sliders['Time'].start, 
                            self.param_info.param_sliders['Time'].end, 4000)
            self.time = t

            mod = getattr(model, self.paramztn_info.selected_paramztn)(**self.param_info.param_values)
            
            if self.phot_pane.visible == True:
                self.phot_main_data = {}

                if 'GP' in self.paramztn_info.selected_paramztn:
                    self.param_info.param_sliders['Num'].visible = True

                    cel_mod = model.Celerite_GP_Model(mod, 0)

                    # Matern-3/2 parameters
                    log_sig = self.param_info.param_values['gp_log_sigma']

                    if 'gp_rho' in self.paramztn_info.selected_params:
                        log_rho = np.log(self.param_info.param_values['gp_rho'])
                    elif 'gp_log_rho' in self.paramztn_info.selected_params:
                        log_rho = self.param_info.param_values['gp_log_rho']

                    # DDSHO parameters
                    gp_log_Q = np.log(2**-0.5)
                    log_omega0 = self.param_info.param_values['gp_log_omega0']

                    if 'gp_log_S0'in self.paramztn_info.selected_params:
                        log_S0 = self.param_info.param_values['gp_log_S0']
                    elif 'gp_log_omega04_S0' in self.paramztn_info.selected_params:
                        log_S0 = self.param_info.param_values['gp_log_omega04_S0'] - (4 * log_omega0)    
                    elif 'gp_log_omega0_S0' in self.paramztn_info.selected_params:
                        log_S0 = self.param_info.param_values['gp_log_omega0_S0'] - log_omega0

                    # Make fake errors (mimicking OGLE photon noise)
                    flux0 = 4000.0
                    mag0 = 19.0
                    mag_obs = cel_mod.get_value(t)

                    flux_obs = flux0 * 10 ** ((mag_obs - mag0) / -2.5)
                    flux_obs_err = flux_obs ** 0.5
                    mag_obs_err = 1.087 / flux_obs_err

                    # Make GP model
                    m32 = celerite.terms.Matern32Term(log_sig, log_rho)
                    sho = celerite.terms.SHOTerm(log_S0, gp_log_Q, log_omega0)
                    jitter = celerite.terms.JitterTerm(np.log(np.average(mag_obs_err)))
                    kernel = m32 + sho + jitter

                    cel_mod = model.Celerite_GP_Model(mod, 0)
                    gp = celerite.GP(kernel, mean = cel_mod, fit_mean = True)

                    # Single prior sample for fake data
                    gp.compute(t, mag_obs_err)
                    all_samps = gp.sample(size = self.param_info.param_sliders['Num'].value + 1)

                    mag_obs_corr = all_samps[0]

                    # Get prior samples, prior mean, and predictive mean
                    self.phot_main_data['gp_prior_mean'] = mag_obs
                    self.phot_main_data['gp_predict_mean'] = gp.predict(mag_obs_corr, return_cov = False)
                    self.gp_samps = all_samps[1:]

                else:
                    self.param_info.param_sliders['Num'].visible = False
                    self.phot_main_data['phot'] = mod.get_photometry(t)

            if self.ast_pane.visible == True:
                self.ast_main_data = {}

                if 'Show Resolved Images' in self.param_info.plot_checkbox.value:
                    resolved_imgs = mod.get_resolved_astrometry(t)
                    self.ast_main_data['resolved_pspl_1'] = resolved_imgs[0]
                    self.ast_main_data['resolved_pspl_2'] = resolved_imgs[1]

                self.ast_main_data['unlensed_pspl'] = mod.get_astrometry_unlensed(t)
                self.ast_main_data['lensed_pspl'] = mod.get_astrometry(t)

            self._update_plots()
                    
    def _update_plots(self, *events):
        if (self.param_info.lock_trigger == False) and (self.plot_layout.visible == True):
            
            t_idx = np.where(self.time <= self.param_info.param_sliders['Time'].value)[0]
            
            if self.phot_pane.visible == True:
                phot_fig = go.Figure()
                phot_fig.update_xaxes(title = 'Time [MJD]', 
                                      title_font_size = FONTSIZES['plot_axes_labels'],
                                      ticks = 'outside', tickformat = '000',
                                      color = 'white', gridcolor = 'grey')

                phot_fig.update_yaxes(title = 'Magnitude [mag]', 
                                      title_font_size = FONTSIZES['plot_axes_labels'],
                                      ticks = 'outside', autorange = 'reversed',
                                      color = 'white', gridcolor = 'grey')

                phot_fig.update_layout(plot_bgcolor = CLRS['secondary'], 
                                       paper_bgcolor = CLRS['secondary'],
                                       font_size = FONTSIZES['plot_axes_ticks'],
                                       title = dict(text = 'Photometry', y = 0.99,
                                                    font = dict(color = 'white', size = FONTSIZES['plot_title'])),
                                       legend = dict(font_color = 'white',
                                                    grouptitlefont_color = 'white'),
                                       margin = dict(l = 0, r = 0, t = 30, b = 0))
                
                all_phot = []
                for i, key in enumerate(self.phot_main_data.keys()):
                    phot_fig.add_trace(self.phot_traces[key].time_trace(
                        x_data = self.time,
                        y_data = self.phot_main_data[key],
                        time_idx = t_idx,
                        zorder = i
                    ))
                    
                    all_phot += list(self.phot_main_data[key])

                if 'Show Time Markers' in self.param_info.plot_checkbox.value:
                    for i, key in enumerate(self.phot_main_data.keys()):
                        phot_fig.add_trace(self.phot_traces[key].time_marker(
                            x_data = self.time,
                            y_data = self.phot_main_data[key],
                            marker_idx = t_idx[-1],
                            zorder = i
                        ))

                if 'Show Full Traces' in self.param_info.plot_checkbox.value:
                    for i, key in enumerate(self.phot_main_data.keys()):
                        phot_fig.add_trace(self.phot_traces[key].full_trace(
                            x_data = self.time,
                            y_data = self.phot_main_data[key]
                        ))

                if 'GP' in self.paramztn_info.selected_paramztn:
                    # needs to be inside this function to reset cycle
                    clr_cycle = cycle(CLRS['gp_cycle'])
                    for i, samp in enumerate(self.gp_samps):
                        if i == 0:
                            show_legend = True
                            zorder = -1
                        else:
                            show_legend = False
                            zorder = -2
                        
                        phot_fig.add_trace(go.Scatter(
                            x = self.time[t_idx],
                            y = samp[t_idx],
                            name = '', zorder = zorder,
                            legendgroup = 'GP Prior Samples',
                            legendgrouptitle = dict(text = 'GP Prior Samples', font_size = FONTSIZES['legendgroup']),
                            line = dict(width = 0.3, color = next(clr_cycle)),
                            hoverinfo = 'skip', showlegend = show_legend
                        ))
                        
                        all_phot += list(samp)
                
                # Trace to fix axis limits
                min_x, max_x = np.min(self.time), np.max(self.time)
                min_y, max_y = np.min(all_phot), np.max(all_phot)

                phot_fig.add_trace(go.Scatter(
                    x = [min_x, max_x], y = [min_y, max_y],
                    marker = dict(color = 'rgba(0, 0, 0, 0)', size = 10),
                    mode = 'markers', hoverinfo = 'skip', showlegend = False
                ))

                # Update figure
                self.phot_pane.object = phot_fig
            
            if self.ast_pane.visible == True:
                ast_fig = go.Figure()
                ast_fig.update_xaxes(title = '&#916;&#120572;</span><sup>*</sup> [arcsec]', 
                                     title_font_size = FONTSIZES['plot_axes_labels'],
                                     ticks = 'outside', tickformat = '000', 
                                     color = 'white', gridcolor = 'grey') 

                ast_fig.update_yaxes(title = '&#916;&#120575; [arcsec]', 
                                     title_font_size = FONTSIZES['plot_axes_labels'],
                                     ticks = 'outside', 
                                     color = 'white', gridcolor = 'grey')

                ast_fig.update_layout(plot_bgcolor = CLRS['secondary'], 
                                      paper_bgcolor = CLRS['secondary'],
                                      font_size = FONTSIZES['plot_axes_ticks'],
                                      title = dict(text = 'Astrometry', y = 0.99,
                                                    font = dict(color = 'white', size = FONTSIZES['plot_title'])),
                                      legend = dict(font_color = 'white',
                                                    grouptitlefont_color = 'white'),
                                      margin = dict(l = 0, r = 0, t = 30, b = 0))  

                all_ra, all_dec = [], []
                for i, key in enumerate(self.ast_main_data.keys()):
                    ast_fig.add_trace(self.ast_traces[key].time_trace(
                        x_data = self.ast_main_data[key][:, 0],
                        y_data = self.ast_main_data[key][:, 1],
                        text = self.time,
                        time_idx = t_idx,
                        zorder = i
                    ))

                    all_ra += list(self.ast_main_data[key][:, 0])
                    all_dec += list(self.ast_main_data[key][:, 1])

                if 'Show Time Markers' in self.param_info.plot_checkbox.value:
                    for i, key in enumerate(self.ast_main_data.keys()):
                        ast_fig.add_trace(self.ast_traces[key].time_marker(
                            x_data = self.ast_main_data[key][:, 0],
                            y_data = self.ast_main_data[key][:, 1],
                            marker_idx = t_idx[-1],
                            zorder = i
                        ))

                if 'Show Full Traces' in self.param_info.plot_checkbox.value:
                    for i, key in enumerate(self.ast_main_data.keys()):
                        ast_fig.add_trace(self.ast_traces[key].full_trace(
                            x_data = self.ast_main_data[key][:, 0],
                            y_data = self.ast_main_data[key][:, 1],
                            text = self.time
                        ))

                # Trace to fix axis limits
                min_x, max_x = np.min(all_ra), np.max(all_ra)
                min_y, max_y = np.min(all_dec), np.max(all_dec)
                
                ast_fig.add_trace(go.Scatter(
                    x = [min_x, max_x], y = [min_y, max_y],
                    marker = dict(color = 'rgba(0, 0, 0, 0)', size = 10),
                    mode = 'markers', hoverinfo = 'skip', showlegend = False
                ))

                # Update figure
                self.ast_pane.object = ast_fig
        
    def __panel__(self):
        return self.plot_layout


################################################
# Dashboard - Layout
################################################
class Dashboard(Viewer):
    # To be instantiated ParamztnSelect class
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    
    def __init__(self, **params):
        super().__init__(**params)
        
        # Parameter section
        self.param_tabs = ParamTabs(paramztn_info = self.paramztn_info)
        self.param_summary = ParamSummary(paramztn_info = self.paramztn_info, param_info = self.param_tabs)
        self.param_row = pn.Row(self.param_summary, 
                                self.param_tabs, 
                                styles = {'height':'35%'})
        
        # Plot section
        self.plot_row = PlotRow(paramztn_info = self.paramztn_info, param_info = self.param_tabs)
        
        # Entire dashboard layout
        self.dashboard_layout = pn.FlexBox(self.plot_row,
                                           self.param_row,
                                           flex_direction = 'column',
                                           visible = False,
                                           styles = {'padding-left':'1%',
                                                     'padding-right':'1%',
                                                     'min-height':'500px',
                                                     'max-height':'1500px',
                                                     'height':'100vh',
                                                     'width': '100%'})
        
        # Add dependency of checkbox and layout
        self.param_tabs.dashboard_checkbox.param.watch(self._update_layout, 'value')
        self.param_tabs.error_msg.param.watch(self._errored_layout, 'object')
        
    @pn.depends('paramztn_info.selected_paramztn', watch = True)
    def _hide_show(self):
        if self.paramztn_info.selected_paramztn == None:
            self.dashboard_layout.visible = False
        else:
            self.dashboard_layout.visible = True
            
    def _update_layout(self, *events):
        # Is parameter summary checked?
        if 'Parameter Summary' in self.param_tabs.dashboard_checkbox.value:
            self.param_summary.summary_layout.visible = True
            self.param_summary.update_summary()
        else:
            self.param_summary.summary_layout.visible = False
        
        # Are plots checked?
        if set(['Photometry', 'Astrometry']) & set(self.param_tabs.dashboard_checkbox.value) == set():
            self.param_row.styles = {'height':'100%'}
            self.plot_row.phot_pane.visible = False
            self.plot_row.ast_pane.visible = False
            self.plot_row.plot_layout.visible = False 

        # Which plots are checked?
        else:
            self.param_row.styles = {'height':'35%'}
            self.plot_row.plot_layout.visible = True   
            
            if 'Photometry' in self.param_tabs.dashboard_checkbox.value:
                self.plot_row.phot_pane.visible = True
            else:
                self.plot_row.phot_pane.visible = False
                
            if 'Astrometry' in self.param_tabs.dashboard_checkbox.value:
                self.plot_row.ast_pane.visible = True
            else:
                self.plot_row.ast_pane.visible = False 

            self.plot_row.update_traces()
        
    def _errored_layout(self, *events):
        if self.param_tabs.error_msg.object == None:
            self._update_layout()
            
        else:
            self.param_row.styles = {'height':'100%'}
            self.plot_row.plot_layout.visible = False 
            self.param_summary.summary_layout.visible = False
            
                          
    def __panel__(self):
        return self.dashboard_layout

    
################################################
# App Layout
################################################
class BAGLECalc(Viewer):
    page_title = pn.widgets.StaticText(value = 'BAGLE Calculator', 
                                  styles = {'font-size':FONTSIZES['page_title'], 
                                            'font-weight':'600', 
                                            'margin-bottom':'-0.4rem'})
    
    mod_row = ModSelect()
    paramztn_row = ParamztnSelect(mod_info = mod_row)
    dashboard = Dashboard(paramztn_info = paramztn_row)
    
    # Layout for model and parameterization selection rows
    selection_layout = pn.FlexBox(
        pn.layout.Divider(),
        mod_row,
        paramztn_row,
        pn.layout.Divider(),
        flex_direction = 'column',
        align_items = 'center',
        styles = {'width': '90%'}
    )
    
    # Content layout for entire page
    page_content = pn.FlexBox(
        page_title,
        selection_layout,
        dashboard,
        flex_direction = 'column',
        align_items = 'center',
        align_content = 'center',
        styles = {'width': '100%', 
                  'min-width':'1000px',
                  'max-width':'2500px',
                  'height':'fit-content'}
    )

    def __panel__(self):
        # Center content
        return pn.Row(
            pn.HSpacer(),
            self.page_content,
            pn.HSpacer()
        )
    
################################################
# Server App
################################################
BAGLECalc().servable(title = 'BAGLE Calculator')