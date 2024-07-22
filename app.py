################################################
# Packages
################################################
import re
import textwrap
from functools import partial
from itertools import cycle
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from bagle import model
import celerite

import panel as pn
from panel.viewable import Viewer
from panel.theme import Material
from bokeh.models import Tooltip
from bokeh.models.dom import HTML
import param

import globals


################################################
# Initialize Panel
################################################
# Extensions and themes used by panel
pn.extension('tabulator', 'plotly', design = 'bootstrap')
pn.config.theme = 'dark'


################################################
# Model Selection Section
################################################
class ModSelect(Viewer):
    
    # Dictionary to store selection values
    type_dict = param.Dict(default = {})
    
    #######################
    # Panel Components
    #######################
    # Model header
    mod_header = pn.widgets.StaticText(value = 'Model:',
                                       styles = {'font-size': globals.FONTSIZES['header'], 
                                                 'font-weight':'550', 
                                                 'margin-right':'0.9rem'})

    # Model selection boxes
    srclens_type = pn.widgets.Select(name = '', 
                                     options = {'Point-Source Point-Lens': 'PSPL',
                                                'Point-Source Binary-Lens': 'PSBL',
                                                'Binary-Source Point-Lens': 'BSPL',
                                                'Binary-Source Binary-Lens': 'BSBL'}, 
                                     align = 'center', sizing_mode = 'scale_width', 
                                     stylesheets = [globals.DROPDOWN_STYLE])

    data_type = pn.widgets.Select(name = '', 
                                  options = {'Photometry': 'Phot', 
                                             'Astrometry': 'Astrom', 
                                             'Photometry-Astrometry': 'PhotAstrom'}, 
                                  align = 'center', sizing_mode = 'scale_width', 
                                  stylesheets = [globals.DROPDOWN_STYLE])

    par_type = pn.widgets.Select(name = '', 
                                 options = {'No Parallax': 'noPar', 
                                            'Parallax': 'Par'}, 
                                 align = 'center', sizing_mode = 'scale_width', 
                                 stylesheets = [globals.DROPDOWN_STYLE])

    gp_type = pn.widgets.Select(name = '', 
                                options = {'No Gaussian Process': '', 
                                            'Gaussian Process': 'GP'}, 
                                align = 'center', sizing_mode = 'scale_width', 
                                stylesheets = [globals.DROPDOWN_STYLE])
    
    #######################
    # Methods
    #######################
    def __init__(self, **params):
        super().__init__(**params)
        # Initialize type dictionary
        self.update_types()
        
        # Layout of model selection row
        self.mod_layout = self._make_layout()
    
    def _make_layout(self):
        objs = [self.srclens_type, self.data_type, self.par_type, self.gp_type]
        insert_idx = np.arange(1, 2 * len(objs) - 2, 2)
        
        for i in insert_idx:
            plus = pn.widgets.StaticText(name = '', value = '+', align = 'center',
                                         styles = {'font-size':globals.FONTSIZES['plus']})
            objs = np.insert(objs, i, plus) 
            
        
        mod_layout = pn.Row(objects = [self.mod_header] + list(objs),
                            styles = {'padding-left':'10%',
                                      'padding-right':'10%',
                                      'margin-bottom':'0.5rem'})
        return mod_layout
    
    @pn.depends('srclens_type.value', 'data_type.value', 
                'par_type.value', 'gp_type.value', watch = True)
    def update_types(self):
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
    # To be instantiated class (required input)
    mod_info = param.ClassSelector(class_ = ModSelect)
    
    # Current selected paramertization and parameters
    selected_paramztn = param.String(allow_None = True)
    selected_params = param.List()
    selected_phot_params = param.List()
    
    # Dictionary to store buttons
    paramztn_btns = param.Dict(default = {})
    
    #######################
    # Panel Components
    #######################
    # Flex box to display buttons
    paramztn_box = pn.FlexBox(align = 'center')

    # Parameterization Header
    paramztn_header = pn.widgets.StaticText(value = f'Parameterization:', align = 'start',
                                            styles = {'font-size':globals.FONTSIZES['header'],
                                                      'font-weight':'550', 
                                                      'margin-right':'1rem'})
    # Error message in case of no parameterizations
    paramztn_error = pn.widgets.StaticText(
        value = 'ERROR: There are currently no supported parameterizations for this model. Please try a different selection.',
        styles = {'font-size':globals.FONTSIZES['paramztn_error'], 
                  'text-align':'center',
                  'font-weight':'550', 
                  'margin-bottom':'-0.2rem'},
        stylesheets = ['''.bk-clearfix {color: red;}''']
    )
    
    # Layout of parameterization selection row
    paramztn_layout = pn.Row(styles = {'padding-right':'5%', 
                                       'padding-left':'5%',
                                       'margin-bottom':'-0.3rem'})
    
    #######################
    # Methods
    #######################
    @pn.depends('mod_info.type_dict', watch = True, on_init = True)
    def update_paramztn(self):
        '''
        Updates the contents of the parameterization selection row of the page.
        '''  
        mod_types = self.mod_info.type_dict
        
        # Clear selected parameterization
        self.selected_paramztn = None
        
        # Get paramaterizations for selected model   
        if mod_types['gp'] == '':
            mod_regex = '_'.join([mod_types[key] for key in mod_types.keys() 
                                  if key != 'gp']) + '_Param'
        elif mod_types['gp'] == 'GP':
            mod_regex = '_'.join(list(mod_types.values())) + '_Param'

        mod_paramztns = [mod for mod in globals.ALL_MODS if re.match(mod_regex, mod)]
            
        # No parameterizations found for selected model
        if len(mod_paramztns) == 0:
            self.paramztn_layout.objects = [pn.HSpacer(), self.paramztn_error, pn.HSpacer()]
            
        # Parameterizations found for selected model
        else:
            for paramztn in mod_paramztns:
                # Check if button exists
                if paramztn in self.paramztn_btns.keys():
                    # Reset style of existing button
                    self.paramztn_btns[paramztn].stylesheets = [globals.BASE_BTN_STYLE]

                else:
                    # Write HTML for button tooltip
                    all_param_names = self.get_param_names(paramztn, mod_types)

                    tooltip_html = ''.join([f'''<span>{param}</span>''' for param in all_param_names])
                    tooltip_html = HTML(f'''
                        <div style = "display:flex; align-items:center; flex-direction:column; 
                                      padding:0.25rem; border:0.04rem black solid; color:{globals.CLRS['main']};
                                      font-size:{globals.FONTSIZES['tooltip']}; font-weight:bold;">
                            {tooltip_html}
                        </div>
                    ''')

                    # Create parameterization button
                    self.paramztn_btns[paramztn] = pn.widgets.Button(name = paramztn, button_type = 'primary', 
                                                                     description = (Tooltip(content = tooltip_html, 
                                                                                            position = 'bottom')),
                                                                     stylesheets = [globals.BASE_BTN_STYLE])

                # Add/Update on-click action for button
                self.paramztn_btns[paramztn].on_click(partial(self._change_selected_btn, 
                                                              mod_types = mod_types))
            # Get relevant buttons and update paramztn_box
            self.paramztn_box.objects = [self.paramztn_btns[key] for key in mod_paramztns]
            self.paramztn_layout.objects = [self.paramztn_header, self.paramztn_box]
            
    def get_param_names(self, paramztn, mod_types, return_phot_names = False):
        # Get paramaterization class
        class_num = re.search('Param.*', paramztn).group()
        if mod_types['gp'] == 'GP':
            param_class_str = '_'.join([mod_types['srclens'], 'GP', mod_types['data'] + class_num])
        else:
            param_class_str = '_'.join([mod_types['srclens'], mod_types['data'] + class_num])

        param_class = getattr(model, param_class_str)
        
        # Get required parameters for paramaterization
        all_param_names = (param_class.fitter_param_names + param_class.phot_param_names + 
                           param_class.phot_optional_param_names + param_class.ast_optional_param_names)
        
        if mod_types['par'] == 'Par':
            all_param_names += ['raL', 'decL']
        
        # Check if phot_names should be returned
        if return_phot_names == True:
            return param_class.phot_param_names, all_param_names
        else:
            return all_param_names
    
    def _change_selected_btn(self, event, mod_types): 
        if (event.obj.name != self.selected_paramztn):
            # Reset CSS of old selected button if it exists
            if self.selected_paramztn != None:
                self.paramztn_btns[self.selected_paramztn].stylesheets = [globals.BASE_BTN_STYLE]
            
            # Change CSS of new selected button
            event.obj.stylesheets = [globals.SELECTED_BTN_STYLE]

            # Update selected parameters and parameterization
            self.selected_paramztn = event.obj.name
            self.selected_phot_params, self.selected_params = self.get_param_names(event.obj.name, mod_types, 
                                                                                   return_phot_names = True)
            
    def __panel__(self):
        return self.paramztn_layout


################################################
# Dashboard - Parameter Tabs
################################################
class ParamTabs(Viewer):
    # To be instantiated classes (required inputs)
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    
    # Parameters to prevent unwanted updates or trigger updates
        # It might be better to make lock_trigger into a dictionary to store locks for different components
        # Currently not needed, but this could separate Time slider lock and checkbox lock (see update functions in PlotRow class)
    lock_trigger, trigger_param_change = param.Boolean(), param.Boolean()
    
    # Current model slider object being changed by user
    current_mod_slider = None

    # Dictionary for parameter values
    param_values = param.Dict(default = {})
    
    #######################
    # Panel Components
    #######################
    # Dictionary to store all sliders and watchers. 
        # Note: This is needed so that we don't always create new sliders and lag the page from memory leaks.
    param_sliders, slider_watchers = {}, {}
    
    # Time and number of point sliders (for all models)
    param_sliders['Time'] = pn.widgets.FloatSlider(name = 'Time [MJD]',
                                                   format = '1[.]000',
                                                   margin = (10, 12, -2, 12),
                                                   design = Material,
                                                   stylesheets = [globals.BASE_SLIDER_STYLE])

    param_sliders['Num_pts'] = pn.widgets.IntSlider(name = 'Number of Points (Trace Resolution)',
                                                    start = 1000, value = 3500, end = 20000, step = 100,
                                                    format = '1[.]000',
                                                    margin = (10, 12, -2, 12),
                                                    design = Material,
                                                    stylesheets = [globals.BASE_SLIDER_STYLE])

    # Slider used for GP prior samples
    param_sliders['Num_samps'] = pn.widgets.IntSlider(name = 'Number of GP Samples',
                                                      start = 0, value = 3, end = 10, step = 1,
                                                      visible = False,
                                                      format = '1[.]000',
                                                      margin = (10, 0, -2, 12),
                                                      design = Material,
                                                      stylesheets = [globals.BASE_SLIDER_STYLE])
    
    # Layout for model-dependent sliders
    mod_sliders = pn.FlexBox(flex_wrap = 'wrap', styles = {'margin-bottom':'2rem'})
    
    # Layout for sliders that are present in all models
    const_sliders = pn.FlexBox(param_sliders['Time'], 
                               param_sliders['Num_pts'],
                               flex_wrap = 'wrap')
    # Layout for all sliders
    sliders_layout = pn.Column(const_sliders,
                               param_sliders['Num_samps'],
                               pn.layout.Divider(),
                               mod_sliders,
                               name = 'Parameter Sliders',
                               styles = {'overflow':'scroll', 'height':'100%'})
        
    # Table for slider range settings
    range_table = pn.widgets.Tabulator(name = 'Slider Settings',
                                       text_align = 'left', layout = 'fit_columns',
                                       editors = {'Units': None}, 
                                       sizing_mode = 'stretch_both',
                                       stylesheets = [globals.TABLTR_STYLE])
    
    # HTML message for errored slider range settings
    error_msg = pn.pane.HTML(object = None, name = 'ERRORED SLIDERS')
    
    # Checkbox for dashboard panes
    db_options_dict = {
        'Phot': {'Photometry': 'phot', 
                 'Parameter Summary': 'summary'},

        'Astrom': {'Astrometry':'ast', 
                   'Parameter Summary':'summary'},

        'PhotAstrom': {'Photometry':'phot', 
                       'Astrometry':'ast', 
                       'Parameter Summary':'summary'}
    }
    dashboard_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{globals.FONTSIZES['header']}"><u><b>Dashboard Layout</b></u></span>''',
        styles = {'color':'white', 'max-height':'min-content'}
    )
    dashboard_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
    dashboard_settings = pn.Column(dashboard_settings_header, 
                                   dashboard_checkbox, 
                                   styles = {'margin':'0.5rem'})
    
    # Checkbox for general plot settings
    genrl_plot_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{globals.FONTSIZES['header']}"><u><b>General Plot Settings</b></u></span>''',
        styles = {'color':'white', 'max-height':'min-content'}
    )
    genrl_plot_checkbox = pn.widgets.CheckBoxGroup(options = {'Show Time Markers': 'marker', 
                                                              'Show Full Traces': 'full_trace'},
                                                   inline = False, align = 'center')
    genrl_plot_settings = pn.Column(genrl_plot_settings_header, 
                                    genrl_plot_checkbox, 
                                    styles = {'margin':'0.5rem'})
    
    
    # Checkbox for photometry settings (currently no options to add)
    phot_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{globals.FONTSIZES['header']}"><u><b>Photometry Plot Settings</b></u></span>''',
        styles = {'color':'white', 'max-height':'min-content'}
    )
    phot_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
    phot_settings = pn.Column(phot_settings_header, 
                              phot_checkbox, 
                              styles = {'margin':'0.5rem'})
    
    # Checkbox for astrometry settings
    ast_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{globals.FONTSIZES['header']}"><u><b>Astrometry Plot Settings</b></u></span>''',
        styles = {'color':'white', 'max-height':'min-content'}
    )
    ast_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
    ast_settings = pn.Column(ast_settings_header, 
                             ast_checkbox, 
                             styles = {'margin':'0.5rem'})
    
    # Layout for settings tab
    settings_layout = pn.FlexBox(dashboard_settings, 
                                 genrl_plot_settings, 
                                 phot_settings,
                                 ast_settings,
                                 name = 'Other Settings',
                                 justify_content = 'center',
                                 styles = {'overflow':'scroll'})
        

    # Layout for entire tab section
    tabs_layout = pn.Tabs(styles = {'border':'white solid 0.08rem',
                                    'background':globals.CLRS['secondary'],
                                    'margin':'0.2rem', 'margin-bottom':'0.1rem'})
    
    #######################
    # Methods
    #######################
    def _check_genrl_errors(self, param, default_val, min_val, max_val, step_val):
        error_html = ''''''
        if np.any(np.isnan([default_val, min_val, max_val, step_val])):
            error_html += '''<li>Range inputs must be a number.</li>'''     
        if (min_val >= max_val):
            error_html += '''<li>The minimum value must be smaller than the maximum value</li>'''
        if ((default_val < min_val) or (default_val > max_val)):
            error_html += '''<li>The default value is not inside the range</li>'''
        if (step_val > (abs(max_val - min_val))):
            error_html += '''<li>The step size cannot be larger than the range size</li>'''

        # Make error message and exit if error exists
        if error_html != '''''':
            error_param = f'''<span style="color:#ff9999";>{param}</span>'''
            self.error_msg.object = f'''
                <span style="color:red; font-size:{globals.FONTSIZES['error_title']};"">Errors in {error_param} Slider:</span>
                <ul style="color:white; font-size:{globals.FONTSIZES['error_txt']};">{error_html}</ul>
            '''
            
            # Force the function that called this function to exit
            sys.exit()
    
    def set_errored_layout(self):
        self.tabs_layout.objects = [self.error_msg, self.range_table]
        self.tabs_layout.stylesheets = [globals.ERRORED_TABS_STYLE]
        
    @pn.depends('paramztn_info.selected_params', watch = True)
    # Note: dependency is set on 'selected_params' instead of 'selected_paramztn' to prevent errors when selected_paramztn = None
    def update_table_and_checks(self):
        mod_types = self.paramztn_info.mod_info.type_dict
        selected_paramztn = self.paramztn_info.selected_paramztn
            
        # Update checkboxes
        # Note: Lock used to not trigger checkbox-related changes
            # This is needed because same changes will trigger through data frame update (leads to 'trigger_param_change')
        self.lock_trigger = True
        
        # Check for GP
        if 'GP' in mod_types['gp']:
            phot_options = {'Show GP Prior Samples': 'gp_samps'}
            
            self.phot_checkbox.param.update(options = phot_options, value = ['gp_samps'])
            self.phot_settings.visible = True
            
        else:
            self.phot_checkbox.value = []
            self.phot_settings.visible = False
        
        # Check for astrometry
        if 'Astrom' in mod_types['data']:
            # Check if binary-source
            if 'BS' in mod_types['srclens']:  
                ast_options = {'Show Resolved, Unlensed Astrometry': 'res_bs_unlen',
                               'Show Resolved Primary Source Images': 'res_bs_len_pri',
                               'Show Resolved Secondary Source Images': 'res_bs_len_sec',
                               'Show Position of Lens(es)': 'lens'}
            else:
                ast_options = {'Show Resolved Source Images': 'res_ps_len',
                               'Show Position of Lens(es)': 'lens'}
                                               
            self.ast_checkbox.param.update(options = ast_options, value = [])
            self.ast_settings.visible = True
        
        # Data type is photometry-only
        else:
            self.ast_settings.visible = False
        
        db_options = self.db_options_dict[mod_types['data']]
        self.dashboard_checkbox.param.update(options = db_options, value = list(db_options.values()))  
        self.genrl_plot_checkbox.param.update(value = ['marker', 'full_trace'])

        self.lock_trigger = False
        
        # Update range data frame
        idx_list = ['Time'] + self.paramztn_info.selected_params
        range_df = pd.DataFrame.from_dict(globals.DEFAULT_RANGES, orient = 'index').loc[idx_list]
        range_df.columns = ['Units', 'Default', 'Min', 'Max', 'Step']
        range_df.index.name = 'Parameter'
        
        self.range_table.value = range_df
        
        # Reset tab to parameter sliders tab
        # The scroll of the parameter sliders tab sometimes bugs if it directly set with 'active'
            # For some reason setting 'active = 1' (or some other tab) first seems to fix this
        self.tabs_layout.active = 1
        self.tabs_layout.active = 0
        
    @pn.depends('range_table.value', watch = True)
    def update_sliders(self):
        df = self.range_table.value
        mod_types = self.paramztn_info.mod_info.type_dict

        # Update constant sliders (i.e. Time, Num_pts, Num_samps)
        default_val = df.loc['Time'].iloc[1]   
        min_val = df.loc['Time'].iloc[2]
        max_val = df.loc['Time'].iloc[3]
        step_val = df.loc['Time'].iloc[4]

        # Check for errors
        try:
            self._check_genrl_errors('Time', default_val, min_val, max_val, step_val)           
        except SystemExit:
            return
    
        # Note: Lock is needed because initial trace changes will be applied by
            # the initialized param value dictionary (leads to 'trigger_param_change')
        self.lock_trigger = True
        self.param_sliders['Time'].param.update(value = default_val,
                                                start = min_val, 
                                                end = max_val,
                                                step = step_val)    

        if 'BL' in mod_types['srclens']:
            self.param_sliders['Num_pts'].param.update(value = 1500)
        else:
            self.param_sliders['Num_pts'].param.update(value = 3000)

        if 'GP' in mod_types['gp']:
            self.param_sliders['Num_samps'].visible = True
            self.param_sliders['Num_samps'].param.update(value = 3)
        else:
            self.param_sliders['Num_samps'].visible = False
            
        self.lock_trigger = False

        # Create/Update model-related sliders
        for param in self.paramztn_info.selected_params:
            units = df.loc[param].iloc[0]
            default_val = df.loc[param].iloc[1]   
            min_val = df.loc[param].iloc[2]
            max_val = df.loc[param].iloc[3]
            step_val = df.loc[param].iloc[4]

            # Check for errors
            try:
                self._check_genrl_errors(param, default_val, min_val, max_val, step_val)             
            except SystemExit:
                return
        
            # Update if slider already exists
            if param in self.param_sliders:
                # Unwatch before updating to prevent multiple repeated watchers (memory leaks)
                self.param_sliders[param].param.unwatch(self.slider_watchers[param])
                self.param_sliders[param].param.update(value = default_val, 
                                                       start = min_val, 
                                                       end = max_val,
                                                       step = step_val)
            # Create slider if it doesn't exist
            else:
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
                                                   margin = (10, 12, 10, 12),
                                                   design = Material,
                                                   stylesheets = [globals.BASE_SLIDER_STYLE])

            # Make watcher for slider
            # Note: throttled is enabled for binary lens because computation time is significantly longer
            if 'BL' in mod_types['srclens']:
                self.slider_watchers[param] = self.param_sliders[param].param.watch(self.update_param_values, 
                                                                                    'value_throttled')
            else:
                self.slider_watchers[param] = self.param_sliders[param].param.watch(self.update_param_values, 
                                                                                    'value')
        
        # Get relevant sliders and update slider_box
        self.mod_sliders.objects = [self.param_sliders[key] for key in self.paramztn_info.selected_params]
        
        # Change slider tab back to non-errored format
        self.tabs_layout.objects = [self.sliders_layout, self.range_table, self.settings_layout]
        self.tabs_layout.stylesheets = [globals.BASE_TABS_STYLE]

        # Initialize param values
        self.update_param_values()
        
        # Clear error message if no errors
        self.error_msg.object = None

    def update_param_values(self, *event):
        # Note: the '*event' argument is used to set dependency on sliders

        if event != ():
            self.current_mod_slider = event[0].obj

        # Update model parameter values
        temp_dict = {}
        for param in self.paramztn_info.selected_params:
            # phot_name parameters should be inputed as an ndarray/list
            if param in self.paramztn_info.selected_phot_params:
                temp_dict[param] = np.array([self.param_sliders[param].value])
            else:
                temp_dict[param] = self.param_sliders[param].value

        self.param_values = temp_dict

        # Note: a trigger is used because if self.param_values doesn't change, updates don't occur
            # An example of this is changing slider 'Min/Max/Step', but not the slider value (i.e. 'Default')
            # I think this could also be resolved by using 'onlychanged = False' in the lower-level '.param.watch',
                # instead of using '@pn.depends,' but that may make readability more confusing.
                # See: https://param.holoviz.org/user_guide/Dependencies_and_Watchers.html#watchers
        self.trigger_param_change = not self.trigger_param_change

    def __panel__(self):
        return self.tabs_layout
    

################################################
# Dashboard - Parameter Summary
################################################ 
class ParamSummary(Viewer):
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    param_info = param.ClassSelector(class_ = ParamTabs)
    
    #######################
    # Panel Components
    #######################
    # Box for parameter summaries (model and derived)
    mod_pane = pn.pane.HTML(styles = {'color':'white', 'max-height':'min-content', 'padding':'0.5rem'})
    derived_pane = pn.pane.HTML(styles = {'color':'white', 'max-height':'min-content', 'padding':'0.5rem'})
    
    # Layout for summary pane
    summary_layout = pn.FlexBox(mod_pane, 
                                derived_pane, 
                                justify_content = 'center',
                                sizing_mode = 'stretch_both',
                                styles = {'border':'white solid 0.08rem', 
                                          'overflow':'scroll',
                                          'background':globals.CLRS['secondary'],
                                          'margin':'0.2rem', 'margin-bottom':'0.1rem'})   
    
    #######################
    # Methods
    #######################
    @pn.depends('summary_layout.visible', 'param_info.trigger_param_change', watch = True)
    def update_summary(self):
        if (self.param_info.lock_trigger == False) and (self.summary_layout.visible == True):
            # Model parameter summary
            mod_html = ''''''
            for param in self.paramztn_info.selected_params:
                if globals.DEFAULT_RANGES[param][0] == None:
                    label = param
                else:
                    label = f'{param} [{globals.DEFAULT_RANGES[param][0]}]'
                
                if param in self.paramztn_info.selected_phot_params:
                    val = self.param_info.param_values[param][0]
                else:
                    val = self.param_info.param_values[param]
                
                mod_html += f'''<span style="font-size:{globals.FONTSIZES['summary_txt']}"><b>{label}</b>:  {round(val, 5)}</span>'''
            mod_html = f'''
                <div style="display:flex; flex-direction:column; align-items:start;">
                    <span style="font-size:{globals.FONTSIZES['header']}"><u><b>Model Parameters</b></u></span>
                    {mod_html}
                </div>           
            '''
            self.mod_pane.object = mod_html

            # Derived parameter summary 
            mod = getattr(model, self.paramztn_info.selected_paramztn)(**self.param_info.param_values)
            all_params_dict = vars(mod)
            
            derived_html = ''''''
            for param in all_params_dict.keys():
                if param not in self.paramztn_info.selected_params + ['raL', 'decL', 'use_gp_phot', 'root_tol']:
                    clr = 'white'
                    if globals.DEFAULT_RANGES[param][0] == None:
                        label = param
                    else:
                        label = f'{param} [{globals.DEFAULT_RANGES[param][0]}]'
                    
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
                    
                    derived_html += f'''<span style="font-size:{globals.FONTSIZES['summary_txt']}"><b style="color:{clr}">{label}</b>:  {val}</span>'''
                    
            derived_html = f'''
                <div style="display:flex;flex-direction:column;align-items:start;">
                    <span style="font-size:{globals.FONTSIZES['header']}"><u><b>Derived Parameters</b></u></span>
                    {derived_html}
                </div>           
            '''     
            self.derived_pane.object = derived_html
         
    def __panel__(self):
        return self.summary_layout
    

################################################
# Dashboard - Plots
################################################
class Trace:   
    def __init__(self, legend_group,
                 primary_clr = None, secondary_clr = None, 
                 time_width = None, full_width = None, marker_size = None,
                 hover_format = None, hover_info = None, full_dash_style = 'dash'):
        '''
        legend_group: a string for the legend group. All traces will be placed under this label.
        
        primary_clr: a string for color of time/marker trace.
        secondary_clr: a string for color of time trace
              
        time_width: a numeric for width of time trace.
        full_width: a numeric for width of full trace.
        marker_size: a numeric for size of marker trace.
        
        hover_format: a HTML string for hover tooltip format for time/full trace. Default is None.
        
        hover_info: a string for the plotly hoverinfo option for time/full trace (see plotly for documentation).
                    This refers to the info that is show on hover tooltip be shown on the graph if hover_format is None.
                    If hover_info = 'skip', and hover_format = None, the hover tooltip will not be shown.
                    
        full_dash_style: a string for the dash style for the full trace (see plotly for documentation).
        
        '''
        self.legend_group = legend_group
        self.primary_clr, self.secondary_clr = primary_clr, secondary_clr,
        self.time_width, self.marker_size, self.full_width = time_width, marker_size, full_width
        self.hover_format, self.hover_info = hover_format, hover_info
        self.full_dash_style = full_dash_style
        
    def time_trace(self, x_data, y_data, time_idx, zorder, trace_clr = None, show_legend = True, text = None):
        '''
        x_data: a list/array for the full data set for x-axis
        y_data: a list/array for the full data set for y-axis
        time_idx: a list/array the set of indices to plot.
        '''
        trace_clr = trace_clr or self.primary_clr
        trace = go.Scatter(x = x_data[time_idx], 
                           y = y_data[time_idx], 
                           name = '', mode = 'lines', zorder = zorder,
                           legendgroup = self.legend_group, showlegend = show_legend,
                           legendgrouptitle = dict(text = self.legend_group, font_size = globals.FONTSIZES['legendgroup']),
                           line = dict(color = trace_clr, width = self.time_width),
                           text = text, hoverinfo = self.hover_info, hovertemplate = self.hover_format)
        return trace

    def full_trace(self, x_data, y_data, trace_clr = None, text = None):
        '''
        x_data: a list/array the full data set for x-axis
        y_data: a list/array the full data set for y-axis
        '''
        trace_clr = trace_clr or self.secondary_clr
        trace =  go.Scatter(x = x_data, 
                            y = y_data,
                            name = '', mode = 'lines', zorder = -10,
                            legendgroup = self.legend_group, showlegend = False, 
                            line = dict(color = trace_clr, width = self.full_width, dash = self.full_dash_style),
                            text = text, hoverinfo = self.hover_info, hovertemplate = self.hover_format)

        return trace

    def time_marker(self, x_data, y_data, marker_idx, zorder, trace_clr = None):
        '''
        x_data: a list/array the full data set for x-axis
        y_data: a list/array the full data set for y-axis
        marker_idx: a nonnegative integer for the index to plot
        '''
        trace_clr = trace_clr or self.primary_clr
        trace = go.Scatter(x = [x_data[marker_idx]], 
                           y = [y_data[marker_idx]],
                           name = '', zorder = zorder,
                           legendgroup = self.legend_group, showlegend = False,
                           mode = 'markers', marker = dict(color = trace_clr, size = self.marker_size),
                           hoverinfo = 'skip')

        return trace
    
class PlotRow(Viewer):
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    param_info = param.ClassSelector(class_ = ParamTabs)
    
    # Note: Main refers to any data that will have a full trace and a time marker, and isn't dependent on a checkbox.
    phot_main, ast_main = param.Dict(), param.Dict()
    
    # Note: Extra refers to any data that is dependent on a checkbox
        # The choice of data for 'extras' is mainly for performance and stylistic purposes
    phot_extra, ast_extra = param.Dict(), param.Dict()
    
    # 'time' is a numpy array of times
    # 'mod' is an instance of a BAGLE model
    # 'gp' is a numpy array of GP prior samples
    time, mod, gp = None, None, None
    
    phot_traces = {
        'phot': Trace(legend_group = 'Photometry',
                      primary_clr = 'red', secondary_clr = 'rgb(255, 77, 77)', 
                      time_width = 2, full_width  = 1.5, marker_size = 10, 
                      hover_format = globals.PHOT_FORMAT),
        
        'gp_predict_mean': Trace(legend_group = 'GP Predictive Mean',
                                 primary_clr = 'red', secondary_clr = 'rgba(255, 77, 77, 0.8)',
                                 time_width = 1.4, full_width  = 0.9, marker_size = 10, 
                                 hover_format = globals.PHOT_FORMAT, full_dash_style = 'solid'),
        'gp_prior_mean': Trace(legend_group = 'GP Prior Mean',
                               primary_clr = 'orange', secondary_clr = 'rgba(255, 193, 77, 0.8)', 
                               time_width = 1.4, full_width  = 0.9, marker_size = 10, 
                               hover_format = globals.PHOT_FORMAT, full_dash_style = 'solid'),
        
        'gp_samps': Trace(legend_group = 'GP Prior Samples',
                          time_width = 0.3,
                          hover_info = 'skip')
        
    }
    
    ast_traces = {
        'lens': Trace(legend_group = 'Lens(es)', 
                      primary_clr = 'black', secondary_clr = 'rgb(26, 26, 26)',
                      time_width = 2, full_width  = 1.5, marker_size = 10, 
                      hover_format = globals.AST_FORMAT),
        
        'unres_len': Trace(legend_group = 'Unresolved, Lensed Source(s)',
                           primary_clr = 'red', secondary_clr = 'rgb(255, 77, 77)', 
                           time_width = 2, full_width  = 1.5, marker_size = 10, 
                           hover_format = globals.AST_FORMAT),
        'unres_unlen': Trace(legend_group = 'Unresolved, Unlensed Source(s)',
                             primary_clr = 'orange', secondary_clr = 'rgb(255, 193, 77)', 
                             time_width = 1.5, full_width  = 1, marker_size = 8, 
                             hover_format = globals.AST_FORMAT),
        
        'res_ps_len': Trace(legend_group = 'Resolved, Lensed Source Images',
                             primary_clr = 'yellow', secondary_clr = 'rgb(255, 255, 77)', 
                             time_width = 1.2, marker_size = 6, 
                             hover_format = globals.AST_FORMAT),
        
        'res_bs_unlen_pri': Trace(legend_group = 'Resolved, Unlensed Primary Source',
                                  primary_clr = 'rgb(0, 134, 149)', secondary_clr = 'rgb(77, 237, 255)', 
                                  time_width = 2, full_width  = 1.5, marker_size = 10, 
                                  hover_format = globals.AST_FORMAT),
        'res_bs_unlen_sec': Trace(legend_group = 'Resolved, Unlensed Secondary Source',
                                  primary_clr = 'rgb(148, 52, 110)', secondary_clr = 'rgb(209, 123, 174)', 
                                  time_width = 2, full_width  = 1.5, marker_size = 10, 
                                  hover_format = globals.AST_FORMAT),
        
        'res_bs_len_pri': Trace(legend_group = 'Resolved, Lensed Primary Source',
                                primary_clr = 'rgb(128, 242, 255)',
                                time_width = 1.2, marker_size = 6, 
                                hover_info = 'skip'),
        'res_bs_len_sec': Trace(legend_group = 'Resolved, Lensed Secondary Source',
                                primary_clr = 'rgb(222, 161, 197)',
                                time_width = 1.2, marker_size = 6, 
                                hover_info = 'skip')
    }
    
    def __init__(self, **params):
        # Set up function dictionaries for extra photometry and astrometry traces
        # The functions in this dictionary should do three things: 
            # 1) update traces
            # 2) plot the traces
            # 3) return the photometry/RA/DEC data as a single 1D list
        self.phot_extra_fns = {
            'gp_samps': self._update_gp_samps
        }
        
        self.ast_extra_fns = {
            'lens': self._update_lens,
            'res_ps_len': self._update_res_ps_len,
            'res_bs_unlen': self._update_res_bs_unlen,
            'res_bs_len_pri': partial(self._update_res_bs_len, src_idx = 0),
            'res_bs_len_sec': partial(self._update_res_bs_len, src_idx = 1)
        }
        
        # Plot row layout
        self.phot_pane = pn.pane.Plotly(config = globals.PHOT_CONFIGS,
                                        sizing_mode = 'stretch_both',
                                        visible = False,
                                        styles = {'border':'white solid 0.08rem', 
                                                  'background':globals.CLRS['secondary'],
                                                  'margin':'0.2rem',
                                                  'padding':'0.5rem', 'padding-right':'0'})

        self.ast_pane = pn.pane.Plotly(config = globals.AST_CONFIGS,
                                       sizing_mode = 'stretch_both',
                                       visible = False,
                                       styles = {'border':'white solid 0.08rem', 
                                                 'background':globals.CLRS['secondary'],
                                                 'margin':'0.2rem',
                                                 'padding':'0.5rem', 'padding-right':'0'})
        
        self.set_initial_figs()
        self.plot_layout = pn.Row(self.phot_pane, 
                                  self.ast_pane, 
                                  styles = {'height':'65%'})
        
        # Define slider-related dependencies
            # This is only used because @pn.depends with dictionary values doesn't work well
        super().__init__(**params)
        self.param_info.param_sliders['Num_pts'].param.watch(self.update_mod_components, 'value')
        
        self.param_info.param_sliders['Num_samps'].param.watch(self._update_phot_extra_traces, 'value')
        self.param_info.param_sliders['Num_samps'].param.watch(self.update_phot_plot, 'value')
        
        self.param_info.param_sliders['Time'].param.watch(self.update_phot_plot, 'value')
        self.param_info.param_sliders['Time'].param.watch(self.update_ast_plot, 'value')
        
    def set_initial_figs(self):
        # This is an initial empty figure for stylistic purposes (not really necessary)
        init_fig = go.Figure(layout = dict(plot_bgcolor = globals.CLRS['secondary'],
                                           paper_bgcolor = globals.CLRS['secondary']))
        init_fig.update_xaxes(showgrid = False, zeroline = False, showticklabels = False)
        init_fig.update_yaxes(showgrid = False, zeroline = False, showticklabels = False)
        
        self.phot_pane.object = init_fig
        self.ast_pane.object = init_fig
    
    @pn.depends('param_info.trigger_param_change', watch = True) 
    def update_mod_components(self, *event):
        # Note: '*event' is needed for 'Num_pts' watcher
        
        # Note: lock needed to guard against Num_pts slider reset because trigger_param_change also triggers the update
            # See chain: update_table_and_checks => update_sliders => update_param_values in ParamTabs class
        if self.param_info.lock_trigger == False:
            self.time = np.linspace(start = self.param_info.param_sliders['Time'].start, 
                                    stop = self.param_info.param_sliders['Time'].end, 
                                    num = self.param_info.param_sliders['Num_pts'].value)

            self.mod = getattr(model, self.paramztn_info.selected_paramztn)(**self.param_info.param_values)

            event_slider = self.param_info.current_mod_slider
            try:
                # Update photometry if visible
                self._update_phot_main_traces()
                self._update_phot_extra_traces()
                self.update_phot_plot()
                
                # Update astrometry if visible
                self._update_ast_main_traces()
                self._update_ast_extra_traces()
                self.update_ast_plot()

                if event_slider not in [(), None]:
                    for param in self.param_info.param_sliders.keys():
                        self.param_info.param_sliders[param].disabled = False
                    event_slider.stylesheets = [globals.BASE_SLIDER_STYLE]

            except:
                for param in self.param_info.param_sliders.keys():
                    self.param_info.param_sliders[param].disabled = True
                event_slider.param.update(disabled = False, stylesheets = [globals.ERRORED_SLIDER_STYLE])

    ########################
    # Photometry Methods
    ########################                      
    @pn.depends('phot_pane.visible', watch = True)
    def _update_phot_main_traces(self):
        # Note: lock needed to guard against checkbox resets because 'trigger_param_change' also triggers the update
            # Look at update_mod_components for 'trigger_param_change' dependency
            # Also see chain: update_table_and_checks => update_sliders => update_param_values in ParamTabs class
        if (self.param_info.lock_trigger == False) and (self.phot_pane.visible == True):
            selected_params = self.paramztn_info.selected_params
            self.phot_main = {}
            
            # Check for GP
            if 'GP' in self.paramztn_info.selected_paramztn:
                cel_mod = model.Celerite_GP_Model(self.mod, 0)
                
                # Matern-3/2 parameters
                log_sig = self.param_info.param_values['gp_log_sigma']

                if 'gp_rho' in selected_params:
                    log_rho = np.log(self.param_info.param_values['gp_rho'])
                elif 'gp_log_rho' in selected_params:
                    log_rho = self.param_info.param_values['gp_log_rho']

                # DDSHO parameters
                gp_log_Q = np.log(2**-0.5)
                log_omega0 = self.param_info.param_values['gp_log_omega0']

                if 'gp_log_S0'in selected_params:
                    log_S0 = self.param_info.param_values['gp_log_S0']
                elif 'gp_log_omega04_S0' in selected_params:
                    log_S0 = self.param_info.param_values['gp_log_omega04_S0'] - (4 * log_omega0)    
                elif 'gp_log_omega0_S0' in selected_params:
                    log_S0 = self.param_info.param_values['gp_log_omega0_S0'] - log_omega0
    
                # Make fake errors (mimicking OGLE photon noise)
                flux0 = 4000.0
                mag0 = 19.0
                mag_obs = cel_mod.get_value(self.time)

                flux_obs = flux0 * 10 ** ((mag_obs - mag0) / -2.5)
                flux_obs_err = flux_obs ** 0.5
                mag_obs_err = 1.087 / flux_obs_err

                # Make GP model
                m32 = celerite.terms.Matern32Term(log_sig, log_rho)
                sho = celerite.terms.SHOTerm(log_S0, gp_log_Q, log_omega0)
                jitter = celerite.terms.JitterTerm(np.log(np.average(mag_obs_err)))
                kernel = m32 + sho + jitter

                self.gp = celerite.GP(kernel, mean = cel_mod, fit_mean = True)
                self.gp.compute(self.time, mag_obs_err)

                # Use a single prior draw for prior mean
                mag_obs_corr = self.gp.sample(size = 1)[0]
                
                # Get prior mean, and predictive mean
                self.phot_main['gp_prior_mean'] = mag_obs
                self.phot_main['gp_predict_mean'] = self.gp.predict(mag_obs_corr, return_cov = False)
                
            else:
                self.phot_main['phot'] = self.mod.get_photometry(self.time)
                
    def _update_gp_samps(self, trace = False, plot = False,  fig = None, time_idx = None, phot_list = None):
        if trace == True:
            # Note: self.gp.compute should have already been called
            self.phot_extra['gp_samps'] = self.gp.sample(size = self.param_info.param_sliders['Num_samps'].value)
            
        if (plot == True) and (self.param_info.param_sliders['Num_samps'].value > 0):
            # color cycle for samples
            clr_cycle = cycle(globals.CLRS['gp_cycle'])

            # Lists used to only show the legend for the first sample and put it in front for visual purposes
            zorder_list = np.repeat(-101, self.param_info.param_sliders['Num_samps'].value).tolist()
            show_legend_list = np.repeat(False, self.param_info.param_sliders['Num_samps'].value).tolist()
            
            zorder_list[0], show_legend_list[0] = -100, True

            for i, samp in enumerate(self.phot_extra['gp_samps']):
                fig.add_trace(
                    self.phot_traces['gp_samps'].time_trace(
                        x_data = self.time,
                        y_data = samp,
                        time_idx = time_idx,
                        zorder = zorder_list[i],
                        show_legend = show_legend_list[i],
                        trace_clr = next(clr_cycle)
                    )
                )

                phot_list += list(samp)
            
    @pn.depends('phot_pane.visible', 'param_info.phot_checkbox.value', watch = True)
    # Note: this function needs to be defined after '_update_phot_main_traces' to have the proper precedence in @pn.depends
    def _update_phot_extra_traces(self, *event):
        # Note: lock needed to guard against checkbox resets because 'trigger_param_change' also triggers the update
            # Look at update_mod_components for 'trigger_param_change' dependency
            # Also see chain: update_table_and_checks => update_sliders => update_param_values in ParamTabs class
        if (self.param_info.lock_trigger == False) and (self.phot_pane.visible == True):
            
            self.phot_extra = {}
            for key in self.param_info.phot_checkbox.value:
                self.phot_extra_fns[key](trace = True)
                
    @pn.depends('phot_pane.visible', 
                'param_info.phot_checkbox.value', 'param_info.genrl_plot_checkbox.value', watch = True)
    def update_phot_plot(self, *event):
        # Note: '*event' is needed for 'Time' watcher
        
        # Note: lock needed to guard against checkbox and Time slider changes because trigger_param_change also triggers the update
            # Look at update_mod_components for 'trigger_param_change' dependency
            # Also see chain: update_table_and_checks => update_sliders => update_param_values in ParamTabs class
        if (self.param_info.lock_trigger == False) and (self.phot_pane.visible == True):
            t_idx = np.where(self.time <= self.param_info.param_sliders['Time'].value)[0]
            
            phot_fig = go.Figure()
            phot_fig.update_xaxes(title = 'Time [MJD]', 
                                  title_font_size = globals.FONTSIZES['plot_axes_labels'],
                                  ticks = 'outside', tickformat = '000',
                                  color = 'white',
                                  gridcolor = globals.CLRS['gridline'], zeroline = False)

            phot_fig.update_yaxes(title = 'Magnitude [mag]', 
                                  title_font_size = globals.FONTSIZES['plot_axes_labels'],
                                  ticks = 'outside', autorange = 'reversed',
                                  color = 'white',
                                  gridcolor = globals.CLRS['gridline'], zeroline = False)

            phot_fig.update_layout(plot_bgcolor = globals.CLRS['secondary'], 
                                   paper_bgcolor = globals.CLRS['secondary'],
                                   font_size = globals.FONTSIZES['plot_axes_ticks'],
                                   title = dict(text = 'Photometry', y = 0.99,
                                                font = dict(color = 'white', size = globals.FONTSIZES['plot_title'])),
                                   legend = dict(font_color = 'white',
                                                grouptitlefont_color = 'white'),
                                   margin = dict(l = 0, r = 0, t = 30, b = 0))
            
            #################################
            # Main Photometry Traces
            #################################
            # Plot solid time trace and get photometry points for limits
            all_phot = []
            
            # This is a stylistic choice to not show legend of photometry (no-GP) trace
            show_legend_list = np.repeat(True, len(self.phot_main.keys())).tolist()
            if 'phot' in self.phot_main.keys():
                show_legend_list[0] = False
                
            for i, key in enumerate(self.phot_main.keys()):
                phot_fig.add_trace(
                    self.phot_traces[key].time_trace(
                        x_data = self.time,
                        y_data = self.phot_main[key],
                        time_idx = t_idx,
                        zorder = i,
                        show_legend = show_legend_list[i]
                    )
                )

                all_phot += list(self.phot_main[key])
                
            # Plot full trace is checked
            if 'full_trace' in self.param_info.genrl_plot_checkbox.value:
                for i, key in enumerate(self.phot_main.keys()):
                    phot_fig.add_trace(
                        self.phot_traces[key].full_trace(
                            x_data = self.time,
                            y_data = self.phot_main[key]
                        )
                    )
                    
            # Plot marker point if checked
            if 'marker' in self.param_info.genrl_plot_checkbox.value:
                for i, key in enumerate(self.phot_main.keys()):
                    phot_fig.add_trace(
                        self.phot_traces[key].time_marker(
                            x_data = self.time,
                            y_data = self.phot_main[key],
                            marker_idx = t_idx[-1],
                            zorder = i
                        )
                    )
            
            #################################
            # Extra Photometry Traces
            #################################
            for key in self.param_info.phot_checkbox.value:
                self.phot_extra_fns[key](plot = True, fig = phot_fig, time_idx = t_idx, phot_list = all_phot)

            #################################
            # Limit Trace & Update Pane
            #################################
            # This fixes the axis limits so that they don't change with the Time slider
            min_x, max_x = np.nanmin(self.time), np.nanmax(self.time)
            min_y, max_y = np.nanmin(all_phot), np.nanmax(all_phot)
            
            phot_fig.add_trace(
                go.Scatter(
                    x = [min_x, max_x], y = [min_y, max_y],
                    marker = dict(color = 'rgba(0, 0, 0, 0)', size = 10),
                    mode = 'markers', hoverinfo = 'skip', showlegend = False
                )
            )

            # Replace figure in photometry pane
            self.phot_pane.object = phot_fig
            
    #################################
    # Astrometry Methods
    #################################
    @pn.depends('ast_pane.visible', watch = True)
    def _update_ast_main_traces(self):
        # Note: lock needed to guard against checkbox resets becasue trigger_param_change also triggers the update
            # Look at update_table_and_checks => update_sliders => update_param_values in ParamTabs class
        if (self.param_info.lock_trigger == False) and (self.ast_pane.visible == True):
            
            self.ast_main = {}
            
            # Get unresolved astrometry
                # Theses are consistent main traces for all Astrom/PhotAstrom parameterizations
            self.ast_main['unres_unlen'] = self.mod.get_astrometry_unlensed(self.time)
            self.ast_main['unres_len'] = self.mod.get_astrometry(self.time)
    
    def _update_lens(self, trace = False, plot = False, fig = None, time_idx = None,
                     ra_list = None, dec_list = None):
        if trace == True:
            # Check for binary lens
            if 'BL' in self.paramztn_info.selected_paramztn:
                self.ast_extra['lens'] = self.mod.get_resolved_lens_astrometry(self.time)
            elif 'PL' in self.paramztn_info.selected_paramztn:
                self.ast_extra['lens'] = [self.mod.get_lens_astrometry(self.time)]
        
        if plot == True:
            show_legend_list = np.repeat(False, len(self.ast_extra['lens'])).tolist()
            show_legend_list[0] = True
            
            for i, lens in enumerate(self.ast_extra['lens']):
                ra = lens[:, 0]
                dec = lens[:, 1]
                
                # Plot time trace
                fig.add_trace(
                    self.ast_traces['lens'].time_trace(
                        x_data = ra,
                        y_data = dec,
                        time_idx = time_idx,
                        zorder = -10-i,
                        show_legend = show_legend_list[i],
                        text = self.time
                    )
                )
                
                # Plot full trace if checked
                if 'full_trace' in self.param_info.genrl_plot_checkbox.value:
                    fig.add_trace(
                        self.ast_traces['lens'].full_trace(
                            x_data = ra,
                            y_data = dec,
                            text = self.time
                        )
                    )

                # Plot marker point if checked
                if 'marker' in self.param_info.genrl_plot_checkbox.value:
                    fig.add_trace(
                        self.ast_traces['lens'].time_marker(
                            x_data = ra,
                            y_data = dec,
                            marker_idx = time_idx[-1],
                            zorder = -10-i
                        )
                    )

                ra_list += list(ra)
                dec_list += list(dec)
                
    def _update_res_ps_len(self, trace = False, plot = False, fig = None, time_idx = None, 
                        ra_list = None, dec_list = None):
        if trace == True:
            self.ast_extra['res_ps_len'] = self.mod.get_resolved_astrometry(self.time)
        
        if plot == True: 
            # Check for binary lens
            if 'BL' in self.paramztn_info.selected_paramztn:
                num_imgs = 5 # There are at most 5 real images
                data_code_str = '''
                    ra = self.ast_extra['res_ps_len'][:, i, :][:, 0]
                    dec = self.ast_extra['res_ps_len'][:, i, :][:, 1]
                '''
            else:
                num_imgs = 2
                data_code_str = '''
                    ra = self.ast_extra['res_ps_len'][i][:, 0]
                    dec = self.ast_extra['res_ps_len'][i][:, 1]
                '''
                
            show_legend_list = np.repeat(False, num_imgs).tolist()
            show_legend_list[0] = True
            
            for i in range(num_imgs):
                # Execute code to get RA and DEC arrays
                var_dict = {}
                exec(textwrap.dedent(data_code_str), locals(), var_dict)
                
                # Plot time trace
                fig.add_trace(
                    self.ast_traces['res_ps_len'].time_trace(
                        x_data = var_dict['ra'],
                        y_data = var_dict['dec'],
                        time_idx = time_idx,
                        zorder = -10-i,
                        show_legend = show_legend_list[i],
                        text = self.time
                    )
                )
            
                # Plot marker point if checked
                if 'marker' in self.param_info.genrl_plot_checkbox.value:
                    fig.add_trace(
                        self.ast_traces['res_ps_len'].time_marker(
                            x_data = var_dict['ra'],
                            y_data = var_dict['dec'],
                            marker_idx = time_idx[-1],
                            zorder = -10-i
                        )
                    )
                    
                ra_list += list(var_dict['ra'])
                dec_list += list(var_dict['dec'])
                
    def _update_res_bs_unlen(self, trace = False, plot = False, fig = None, time_idx = None, 
                         ra_list = None, dec_list = None):
        if trace == True:
            self.ast_extra['res_bs_unlen'] = self.mod.get_resolved_astrometry_unlensed(self.time)

        if plot == True:
            src_keys = ['res_bs_unlen_pri', 'res_bs_unlen_sec']
            for i in range(2):
                ra = self.ast_extra['res_bs_unlen'][:, i, :][:, 0]
                dec = self.ast_extra['res_bs_unlen'][:, i, :][:, 1]

                # Plot time trace
                fig.add_trace(
                    self.ast_traces[src_keys[i]].time_trace(
                        x_data = ra,
                        y_data = dec,
                        time_idx = time_idx,
                        zorder = -i,
                        text = self.time
                    )
                )

                # Plot full trace if checked
                if 'full_trace' in self.param_info.genrl_plot_checkbox.value:
                    fig.add_trace(
                        self.ast_traces[src_keys[i]].full_trace(
                            x_data = ra,
                            y_data = dec,
                            text = self.time
                        )
                    )

                # Plot marker point if checked
                if 'marker' in self.param_info.genrl_plot_checkbox.value:
                    fig.add_trace(
                        self.ast_traces[src_keys[i]].time_marker(
                            x_data = ra,
                            y_data = dec,
                            marker_idx = time_idx[-1],
                            zorder = -i
                        )
                    )

                ra_list += list(ra)
                dec_list += list(dec)

    def _update_res_bs_len(self, src_idx = 0, trace = False, plot = False, 
                       fig = None, time_idx = None, ra_list = None, dec_list = None):
        if trace == True:
            # Check if 'res_bs_unlen_pri' and 'res_bs_unlen_sec' are already keys in ast_extra
                # This is done to prevent cases where 'get_resolved_astrometry_unlensed' is ran twice
            if not {'res_bs_len_pri', 'res_bs_len_sec'} <= set(self.ast_extra.keys()):
                res_len = self.mod.get_resolved_astrometry(self.time)
                self.ast_extra['res_bs_len_pri'] = res_len[:, 0, :, :]
                self.ast_extra['res_bs_len_sec'] = res_len[:, 1, :, :]
            
        if plot == True:
            if src_idx == 0:
                src_key = 'res_bs_len_pri'
            elif src_idx == 1:
                src_key = 'res_bs_len_sec'
                
            if 'BL' in self.paramztn_info.selected_paramztn:
                num_imgs = 5
            else:
                num_imgs = 2
            
            show_legend_list = [True] + np.repeat(False, num_imgs - 1).tolist()
            for i in range(num_imgs):
                ra = self.ast_extra[src_key][:, i, 0]
                dec = self.ast_extra[src_key][:, i, 1]
                
                # Plot time trace
                fig.add_trace(
                    self.ast_traces[src_key].time_trace(
                        x_data = ra,
                        y_data = dec,
                        time_idx = time_idx,
                        zorder = -10-i,
                        show_legend = show_legend_list[i],
                        text = self.time
                    )
                )
                
                # Plot marker point if checked
                if 'marker' in self.param_info.genrl_plot_checkbox.value:
                    fig.add_trace(
                        self.ast_traces[src_key].time_marker(
                            x_data = ra,
                            y_data = dec,
                            marker_idx = time_idx[-1],
                            zorder = -10-i
                        )
                    )
                
                # Add RA and Dec to list of all RA and all DEC for axis limits
                ra_list += list(ra)
                dec_list += list(dec)
                
    @pn.depends('ast_pane.visible', 'param_info.ast_checkbox.value', watch = True)
    # Note: this function needs to be defined after '_update_ast_main_traces' to have the proper precedence in @pn.depends
    def _update_ast_extra_traces(self):
        # Note: lock needed to guard against checkbox resets because 'trigger_param_change' also triggers the update
            # Look at update_mod_components for 'trigger_param_change' dependency
            # Also see chain: update_table_and_checks => update_sliders => update_param_values in ParamTabs class
        if (self.param_info.lock_trigger == False) and (self.ast_pane.visible == True):
            
            self.ast_extra = {}
            
            for key in self.param_info.ast_checkbox.value:
                self.ast_extra_fns[key](trace = True)
                
    @pn.depends('ast_pane.visible', 
                'param_info.ast_checkbox.value', 'param_info.genrl_plot_checkbox.value', watch = True)           
    def update_ast_plot(self, *event):
        # Note: '*event' is needed for 'Time' watcher
        
        # Note: lock needed to guard against checkbox and Time slider change because trigger_param_change also triggers the update
            # Look at update_mod_components for 'trigger_param_change' dependency
            # Also see chain: update_table_and_checks => update_sliders => update_param_values in ParamTabs class
        if (self.param_info.lock_trigger == False) and (self.ast_pane.visible == True):
            t_idx = np.where(self.time <= self.param_info.param_sliders['Time'].value)[0]
            
            ast_fig = go.Figure()
            ast_fig.update_xaxes(title = '&#916;&#120572;</span><sup>*</sup> [arcsec]', 
                                 title_font_size = globals.FONTSIZES['plot_axes_labels'],
                                 ticks = 'outside', tickformat = '000', 
                                 color = 'white', 
                                 gridcolor = globals.CLRS['gridline'], zeroline = False) 

            ast_fig.update_yaxes(title = '&#916;&#120575; [arcsec]', 
                                 title_font_size = globals.FONTSIZES['plot_axes_labels'],
                                 ticks = 'outside', 
                                 color = 'white', 
                                 gridcolor = globals.CLRS['gridline'], zeroline = False)

            ast_fig.update_layout(plot_bgcolor = globals.CLRS['secondary'], 
                                  paper_bgcolor = globals.CLRS['secondary'],
                                  font_size = globals.FONTSIZES['plot_axes_ticks'],
                                  title = dict(text = 'Astrometry', y = 0.99,
                                                font = dict(color = 'white', size = globals.FONTSIZES['plot_title'])),
                                  legend = dict(font_color = 'white',
                                                grouptitlefont_color = 'white'),
                                  margin = dict(l = 0, r = 0, t = 30, b = 0))
            
            #################################
            # Main Astrometry Traces
            #################################
            all_ra, all_dec = [], []
            
            for i, key in enumerate(self.ast_main.keys()):
                ast_fig.add_trace(
                    self.ast_traces[key].time_trace(
                        x_data = self.ast_main[key][:, 0],
                        y_data = self.ast_main[key][:, 1],
                        time_idx = t_idx,
                        zorder = i,
                        text = self.time,
                    )
                )

                all_ra += list(self.ast_main[key][:, 0])
                all_dec += list(self.ast_main[key][:, 1])
                
            if 'full_trace' in self.param_info.genrl_plot_checkbox.value:
                for i, key in enumerate(self.ast_main.keys()):
                    ast_fig.add_trace(
                        self.ast_traces[key].full_trace(
                            x_data = self.ast_main[key][:, 0],
                            y_data = self.ast_main[key][:, 1],
                            text = self.time
                        )
                    )
                    
            if 'marker' in self.param_info.genrl_plot_checkbox.value:
                for i, key in enumerate(self.ast_main.keys()):
                    ast_fig.add_trace(
                        self.ast_traces[key].time_marker(
                            x_data = self.ast_main[key][:, 0],
                            y_data = self.ast_main[key][:, 1],
                            marker_idx = t_idx[-1],
                            zorder = i
                        )
                    )
                    
            #################################
            # Extra Photometry Traces
            #################################
            for key in self.param_info.ast_checkbox.value:
                self.ast_extra_fns[key](plot = True, fig = ast_fig, time_idx = t_idx, ra_list = all_ra, dec_list = all_dec)

            #################################
            # Limit Trace & Update Pane
            #################################
            # This fixes the axis limits so that they don't change with the Time slider
            min_x, max_x = np.nanmin(all_ra), np.nanmax(all_ra)
            min_y, max_y = np.nanmin(all_dec), np.nanmax(all_dec)

            ast_fig.add_trace(
                go.Scatter(
                    x = [min_x, max_x], y = [min_y, max_y],
                    marker = dict(color = 'rgba(0, 0, 0, 0)',  size = 10),
                    mode = 'markers', hoverinfo = 'skip', showlegend = False
                )
            )

            # Replace figure in astrometry pane
            self.ast_pane.object = ast_fig
            
    def __panel__(self):
        return self.plot_layout
    

################################################
# Dashboard - Layout
################################################
class Dashboard(Viewer):
    # To be instantiated classes (required inputs)
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
        self.db_components = {
            'summary': self.param_summary.summary_layout,
            'phot': self.plot_row.phot_pane,
            'ast': self.plot_row.ast_pane
        }
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
        # Note: this is needed because 'param_tabs' is a class that uses a required input class
        self.param_tabs.dashboard_checkbox.param.watch(self._update_layout, 'value')
        self.param_tabs.error_msg.param.watch(self._errored_layout, 'object')
        
    @pn.depends('paramztn_info.selected_paramztn', watch = True)
    def _hide_show(self):
        if self.paramztn_info.selected_paramztn == None:
            self.dashboard_layout.visible = False
            self.plot_row.set_initial_figs()
            
        else:
            self.dashboard_layout.visible = True
            
    def _update_layout(self, *event):
        unchecked_components = set(self.db_components.keys()) - set(self.param_tabs.dashboard_checkbox.value)

        for key in self.param_tabs.dashboard_checkbox.value:
            self.db_components[key].visible = True

        for key in unchecked_components:
            self.db_components[key].visible = False

        # Hide plot row and expand param row if no plots are checked
        if {'phot', 'ast'} & set(self.param_tabs.dashboard_checkbox.value) != set():
            self.param_row.styles = {'height':'35%'}
            self.plot_row.plot_layout.visible = True
        else:
            self.param_row.styles = {'height':'100%'}
            self.plot_row.plot_layout.visible = False
        
    def _errored_layout(self, *event):
        if self.param_tabs.error_msg.object == None:
            self._update_layout()
            
        else:
            self.param_tabs.set_errored_layout()
            self.param_row.styles = {'height':'100%'}
            
            self.plot_row.plot_layout.visible = False
            self.plot_row.phot_pane.visible = False
            self.plot_row.ast_pane.visible = False
            
            self.param_summary.summary_layout.visible = False
            
                          
    def __panel__(self):
        return self.dashboard_layout
    

################################################
# App Layout
################################################
class BAGLECalc(Viewer):
    page_title = pn.widgets.StaticText(value = 'BAGLE Calculator', 
                                  styles = {'font-size':globals.FONTSIZES['page_title'], 
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