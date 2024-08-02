################################################
# Packages
################################################
import re
from functools import partial
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from BAGLE_Microlensing.src.bagle import model
import celerite

import panel as pn
from panel.viewable import Viewer
from panel.theme import Material
from bokeh.models import Tooltip
from bokeh.models.dom import HTML
import param

import constants
import traces

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
                                       styles = {'font-size': constants.FONTSIZES['header'], 
                                                 'font-weight':'550', 
                                                 'margin-right':'0.9rem'})

    # Model selection boxes
    srclens_type = pn.widgets.Select(name = '', 
                                     options = {'Point-Source Point-Lens': 'PSPL',
                                                'Point-Source Binary-Lens': 'PSBL',
                                                'Binary-Source Point-Lens': 'BSPL',
                                                'Binary-Source Binary-Lens': 'BSBL'}, 
                                     align = 'center', sizing_mode = 'scale_width', 
                                     stylesheets = [constants.DROPDOWN_STYLE])

    data_type = pn.widgets.Select(name = '', 
                                  options = {'Photometry': 'Phot', 
                                             'Astrometry': 'Astrom', 
                                             'Photometry-Astrometry': 'PhotAstrom'}, 
                                  align = 'center', sizing_mode = 'scale_width', 
                                  stylesheets = [constants.DROPDOWN_STYLE])

    par_type = pn.widgets.Select(name = '', 
                                 options = {'No Parallax': 'noPar', 
                                            'Parallax': 'Par'}, 
                                 align = 'center', sizing_mode = 'scale_width', 
                                 stylesheets = [constants.DROPDOWN_STYLE])

    gp_type = pn.widgets.Select(name = '', 
                                options = {'No Gaussian Process': '', 
                                            'Gaussian Process': 'GP'}, 
                                align = 'center', sizing_mode = 'scale_width', 
                                stylesheets = [constants.DROPDOWN_STYLE])
    
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
                                         styles = {'font-size':constants.FONTSIZES['plus']})
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
                                            styles = {'font-size':constants.FONTSIZES['header'],
                                                      'font-weight':'550', 
                                                      'margin-right':'1rem'})
    # Error message in case of no parameterizations
    paramztn_error = pn.widgets.StaticText(
        value = 'ERROR: There are currently no supported parameterizations for this model. Please try a different selection.',
        styles = {'font-size':constants.FONTSIZES['paramztn_error'], 
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

        mod_paramztns = [mod for mod in constants.ALL_MODS if re.match(mod_regex, mod)]
            
        # No parameterizations found for selected model
        if len(mod_paramztns) == 0:
            self.paramztn_layout.objects = [pn.HSpacer(), self.paramztn_error, pn.HSpacer()]
            
        # Parameterizations found for selected model
        else:
            for paramztn in mod_paramztns:
                # Check if button exists
                if paramztn in self.paramztn_btns.keys():
                    # Reset style of existing button
                    self.paramztn_btns[paramztn].stylesheets = [constants.BASE_BTN_STYLE]

                else:
                    # Write HTML for button tooltip
                    all_param_names = self.get_param_names(paramztn, mod_types)

                    tooltip_html = ''.join([f'''<span>{param}</span>''' for param in all_param_names])
                    tooltip_html = HTML(f'''
                        <div style = "display:flex; align-items:center; flex-direction:column; 
                                      padding:0.25rem; border:0.04rem black solid; color:{constants.CLRS['main']};
                                      font-size:{constants.FONTSIZES['tooltip']}; font-weight:bold;">
                            {tooltip_html}
                        </div>
                    ''')

                    # Create parameterization button
                    self.paramztn_btns[paramztn] = pn.widgets.Button(name = paramztn, button_type = 'primary', 
                                                                     description = (Tooltip(content = tooltip_html, 
                                                                                            position = 'bottom')),
                                                                     stylesheets = [constants.BASE_BTN_STYLE])

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

            # Change CSS of new selected button
            event.obj.stylesheets = [constants.SELECTED_BTN_STYLE]

            # Reset CSS of old selected button if it exists
            if self.selected_paramztn != None:
                self.paramztn_btns[self.selected_paramztn].stylesheets = [constants.BASE_BTN_STYLE]

            # Update selected parameters and parameterization
            self.selected_phot_params, self.selected_params = self.get_param_names(event.obj.name, mod_types, 
                                                                                   return_phot_names = True)
            self.selected_paramztn = event.obj.name

    def __panel__(self):
        return self.paramztn_layout


################################################
# Dashboard - Parameter Tabs
################################################
class SettingsTabs(Viewer):
    # To be instantiated classes (required inputs)
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    
    # Parameters to prevent unwanted updates or trigger updates
        # It might be better to make lock_trigger into a dictionary to store locks for different components
        # Currently not needed, but this could separate Time slider lock and checkbox lock (see update functions in PlotRow class)
    lock_trigger, trigger_param_change = param.Boolean(), param.Boolean()
    
    # Current parameter being changes. The default 'Time' is just a placeholder
    current_param_change = 'Time'

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
                                                   stylesheets = [constants.BASE_SLIDER_STYLE])

    param_sliders['Num_pts'] = pn.widgets.IntSlider(name = 'Number of Line Points (Trace Resolution)',
                                                    start = 1000, value = 3500, end = 20000, step = 100,
                                                    format = '1[.]000',
                                                    margin = (10, 12, -2, 12),
                                                    design = Material,
                                                    stylesheets = [constants.BASE_SLIDER_STYLE])

    # Slider used for GP prior samples
    param_sliders['Num_samps'] = pn.widgets.IntSlider(name = 'Number of GP Samples',
                                                      start = 0, value = 3, end = 10, step = 1,
                                                      visible = False,
                                                      format = '1[.]000',
                                                      margin = (10, 0, -2, 12),
                                                      design = Material,
                                                      stylesheets = [constants.BASE_SLIDER_STYLE])
    
    # Layout for model-dependent sliders
    mod_sliders = pn.FlexBox(flex_wrap = 'wrap', styles = {'padding-bottom':'0.5rem', 
                                                           'max-height':'fit-content'})
    
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
                                       stylesheets = [constants.TABLTR_STYLE])
    
    # HTML message for errored slider range settings
    error_msg = pn.pane.HTML(object = None, name = 'ERRORED SLIDERS')
    
    # Checkbox for dashboard panes
    db_options_dict = {
        'Phot': {'Photometry': 'phot', 
                 'Parameter Summary': 'summary'},

        'Astrom': {'RA vs. Dec (Astrometry)':'ast_radec', 
                   'RA vs. Time (Astrometry)':'ast_ra', 
                   'Dec vs. Time (Astrometry)':'ast_dec', 
                   'Parameter Summary':'summary'},

        'PhotAstrom': {'Photometry':'phot', 
                       'RA vs. Dec (Astrometry)':'ast_radec', 
                       'RA vs. Time (Astrometry)':'ast_ra', 
                       'Dec vs. Time (Astrometry)':'ast_dec', 
                       'Parameter Summary':'summary'}
    }
    dashboard_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{constants.FONTSIZES['header']}"><u><b>Dashboard Layout</b></u></span>''',
        styles = {'color':'white', 'margin-bottom': '0'}
    )
    dashboard_note = pn.pane.HTML(
        object = f'''<span style="font-size:{constants.FONTSIZES['table_txt']}"><b>Note:</b> For 3+ plots, scroll to the right.</span>''',
        styles = {'color':'rgb(204, 204, 204)', 'margin-top': '0', 'margin-bottom': '0'}
    )
    dashboard_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'start')
    dashboard_settings = pn.Column(dashboard_settings_header, 
                                   dashboard_note,
                                   dashboard_checkbox, 
                                   styles = {'margin':'0.5rem'})
    
    # Checkbox for general plot settings
    genrl_plot_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{constants.FONTSIZES['header']}"><u><b>General Plot Settings</b></u></span>''',
        styles = {'color':'white', 'margin-bottom': '0'}
    )
    genrl_plot_checkbox = pn.widgets.CheckBoxGroup(options = {'Show Time Markers': 'marker', 
                                                              'Show Full Traces': 'full_trace'},
                                                   inline = False, align = 'start')
    genrl_plot_settings = pn.Column(genrl_plot_settings_header, 
                                    genrl_plot_checkbox, 
                                    styles = {'margin':'0.5rem'})
    
    
    # Checkbox for photometry settings (currently no options to add)
    phot_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{constants.FONTSIZES['header']}"><u><b>Photometry Plot Settings</b></u></span>''',
        styles = {'color':'white', 'margin-bottom': '0'}
    )
    phot_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'start')
    phot_settings = pn.Column(phot_settings_header, 
                              phot_checkbox, 
                              visible = False,
                              styles = {'margin':'0.5rem'})
    
    # Checkbox for astrometry settings
    ast_settings_header = pn.pane.HTML(
        object = f'''<span style="font-size:{constants.FONTSIZES['header']}"><u><b>Astrometry Plot Settings</b></u></span>''',
        styles = {'color':'white', 'margin-bottom': '0'}
    )
    ast_note = pn.pane.HTML(
        object = f'''<span style="font-size:{constants.FONTSIZES['table_txt']}"><b>Note:</b> Lens may not be visible without Time Marker checked.</span>''',
        styles = {'color':'rgb(204, 204, 204)', 'margin-top': '0', 'margin-bottom': '0'}
    )
    ast_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'start', styles={'fontsize':'150px'})

    # Slider for number of markers used for source images
    param_sliders['Num_marks'] = pn.widgets.IntSlider(name = 'Maximum Number of Points Displayed',
                                                      start = 100, value = 300, end = 5000, step = 10,
                                                      visible = False,
                                                      format = '1[.]000',
                                                      align = 'start',
                                                      design = Material,
                                                      styles = {'width':'50%', 'margin-top':'-0.5rem', 'margin-left':'2.5rem'},
                                                      stylesheets = [constants.MARKER_SLIDER_STYLE])
    ast_settings = pn.Column(ast_settings_header, 
                             ast_note,
                             ast_checkbox, 
                             param_sliders['Num_marks'],
                             visible = False,
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
                                    'background':constants.CLRS['secondary']})
    
    #######################
    # Methods
    #######################
    def __init__(self, **params):
        super().__init__(**params)
        # set on-edit function for range table
        self.range_table.on_edit(self.update_param_change)

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
                <span style="color:red; font-size:{constants.FONTSIZES['error_title']};"">Errors in {error_param} Slider:</span>
                <ul style="color:white; font-size:{constants.FONTSIZES['error_txt']};">{error_html}</ul>
            '''
            
            # Force the function that called this function to exit
            sys.exit()

    def update_table_and_checks(self):
        mod_types = self.paramztn_info.mod_info.type_dict
        
        # Update checkboxes
        # Note: Lock used to not trigger checkbox-related changes
            # This is needed because same changes will trigger through data frame update (leads to 'trigger_param_change')
        self.lock_trigger = True
        

        # # Will be use to empty phot checkbox when more options are added
        # self.phot_checkbox.value = []
        # self.phot_settings.visible = False
        
        # Check for astrometry
        if 'Astrom' in mod_types['data']:
            # Check if binary-source
            if 'BS' in mod_types['srclens']:  
                ast_options = {'Show Resolved, Unlensed Astrometry': 'bs_res_unlen',
                               'Show Resolved Primary Source Images': 'bs_res_len_pri',
                               'Show Resolved Secondary Source Images': 'bs_res_len_sec',
                               'Show Position of Lens(es)': 'lens'}
            else:
                ast_options = {'Show Resolved Source Images': 'ps_res_len',
                               'Show Position of Lens(es)': 'lens'}
                                               
            self.ast_checkbox.param.update(options = ast_options, value = [])
            self.param_sliders['Num_marks'].value = 300
            self.ast_settings.visible = True
        
        # Data type is photometry-only
        else:
            self.ast_settings.visible = False
        
        db_options = self.db_options_dict[mod_types['data']]
        db_value = list(set(db_options.values()) - {'ast_ra', 'ast_dec'})
        self.dashboard_checkbox.param.update(options = db_options, value = db_value)  
        self.genrl_plot_checkbox.param.update(value = ['marker', 'full_trace'])

        self.lock_trigger = False
        
        # Update range data frame
        idx_list = ['Time'] + self.paramztn_info.selected_params
        range_df = pd.DataFrame.from_dict(constants.DEFAULT_RANGES, orient = 'index').loc[idx_list]
        range_df.columns = ['Units', 'Default', 'Min', 'Max', 'Step']
        range_df.index.name = 'Parameter'
        
        self.range_table.value = range_df

        # Reset tab to parameter sliders tab
        # The scroll of the parameter sliders tab sometimes bugs if it directly set with 'active'
            # For some reason setting 'active = 1' (or some other tab) first seems to fix this
        self.tabs_layout.active = 1
        self.tabs_layout.active = 0
        
    def update_param_change(self, *event):
        self.current_param_change = self.range_table.value.index[event[0].row]
        # self.tabs_layout.active = 0
        self.update_sliders()
    
    def update_sliders(self):
        df = self.range_table.value
        selected_paramztn = self.paramztn_info.selected_paramztn

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

        if 'BL' in selected_paramztn:
            self.param_sliders['Num_pts'].param.update(value = 1000)
        else:
            self.param_sliders['Num_pts'].param.update(value = 3000)

        if 'GP' in selected_paramztn:
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
                                                                   stylesheets = [constants.BASE_SLIDER_STYLE])

            # Make watcher for slider
            # Note: throttled is enabled for binary lens because computation time is significantly longer
            if 'BL' in selected_paramztn:
                self.slider_watchers[param] = self.param_sliders[param].param.watch(self.update_param_values, 
                                                                                    'value_throttled')
            else:
                self.slider_watchers[param] = self.param_sliders[param].param.watch(self.update_param_values, 
                                                                                    'value')
        
        # Get relevant sliders and update slider_box
        self.mod_sliders.objects = [self.param_sliders[key] for key in self.paramztn_info.selected_params]

        # Initialize param values
        self.update_param_values()
        
        # Clear error message if no errors
        self.error_msg.object = None

    def update_param_values(self, *event):
        # Note: the '*event' argument is used to set dependency on sliders

        if event != ():
            # Regex is needed to get just the parameter name and not the unit
            self.current_param_change = re.match('[^\W\\[]*', event[0].obj.name).group()

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

    def set_base_layout(self):
        self.tabs_layout.objects = [self.sliders_layout, self.range_table, self.settings_layout]
        for object in self.tabs_layout.objects:
            object.visible = True

        self.tabs_layout.stylesheets = [constants.BASE_TABS_STYLE]

    def set_slider_errored_layout(self, undo = False):
        event_slider = self.param_sliders[self.current_param_change]

        if undo == False:
            for param in self.param_sliders.keys():
                self.param_sliders[param].disabled = True
            
            event_slider.param.update(disabled = False,  
                                      stylesheets = [constants.ERRORED_SLIDER_STYLE])

            self.settings_layout.visible = False
            self.tabs_layout.stylesheets = [constants.ERRORED_TABS_STYLE]

        else:
            for param in self.param_sliders.keys():
                self.param_sliders[param].disabled = False
            
            event_slider.stylesheets = [constants.BASE_SLIDER_STYLE]
            self.set_base_layout()

    def set_range_errored_layout(self):
        self.tabs_layout.objects = [self.error_msg, self.range_table, self.settings_layout]
        self.tabs_layout.active = 0
        self.settings_layout.visible = False
        self.tabs_layout.stylesheets = [constants.ERRORED_TABS_STYLE]

    def __panel__(self):
        return self.tabs_layout
    

################################################
# Dashboard - Parameter Summary
################################################ 
class ParamSummary(Viewer):
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    settings_info = param.ClassSelector(class_ = SettingsTabs)
    
    #######################
    # Panel Components
    #######################
    # Box for parameter summaries (model and derived)
    mod_pane = pn.pane.HTML(styles = {'color':'white', 'max-height':'min-content', 'padding':'0.5rem'})
    derived_pane = pn.pane.HTML(styles = {'color':'white', 'max-height':'min-content', 'padding':'0.5rem'})
    
    # Layout for summary pane
    summary_content = pn.FlexBox(mod_pane, 
                                 derived_pane, 
                                 styles = {'min-width':'fit-content'})   
    
    summary_layout = pn.Row(pn.HSpacer(),
                            summary_content,
                            pn.HSpacer(),
                            styles = {'border':'white solid 0.08rem', 
                                      'background':constants.CLRS['secondary'],
                                      'height':'100%',
                                      'overflow':'scroll',})
    
    #######################
    # Methods
    #######################
    @pn.depends('summary_layout.visible', 'settings_info.trigger_param_change', watch = True)
    def update_summary(self):
        if (self.settings_info.lock_trigger == False) and (self.summary_layout.visible == True):
            # Model parameter summary
            mod_html = ''''''
            for param in self.paramztn_info.selected_params:
                if constants.DEFAULT_RANGES[param][0] == None:
                    label = param
                else:
                    label = f'{param} [{constants.DEFAULT_RANGES[param][0]}]'
                
                if param in self.paramztn_info.selected_phot_params:
                    val = self.settings_info.param_values[param][0]
                else:
                    val = self.settings_info.param_values[param]
                
                mod_html += f'''<span style="font-size:{constants.FONTSIZES['summary_txt']}"><b>{label}</b>:  {round(val, 5)}</span>'''
            mod_html = f'''
                <div style="display:flex; flex-direction:column; align-items:start;">
                    <span style="font-size:{constants.FONTSIZES['header']}"><u><b>Model Parameters</b></u></span>
                    {mod_html}
                </div>           
            '''
            self.mod_pane.object = mod_html

            # Derived parameter summary 
            mod = getattr(model, self.paramztn_info.selected_paramztn)(**self.settings_info.param_values)
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
                    
                    derived_html += f'''<span style="font-size:{constants.FONTSIZES['summary_txt']}"><b style="color:{clr}">{label}</b>:  {val}</span>'''
                    
            derived_html = f'''
                <div style="display:flex;flex-direction:column;align-items:start;">
                    <span style="font-size:{constants.FONTSIZES['header']}"><u><b>Derived Parameters</b></u></span>
                    {derived_html}
                </div>           
            '''     
            self.derived_pane.object = derived_html
         
    def __panel__(self):
        return self.summary_layout
    

################################################
# Dashboard - Plots
################################################
class PlotRow(Viewer):
    paramztn_info = param.ClassSelector(class_ = ParamztnSelect)
    settings_info = param.ClassSelector(class_ = SettingsTabs)

    # 'time' is a numpy array of times
    # 'mod' is an instance of a BAGLE model
    # 'gp' is a celerite GP object with gp.compute performed
    time, mod, gp = None, None, None

    # complex image position and amplification arrays for binary lens models (these are numpy arrays)
    bl_image_arr, bl_amp_arr = None, None

    # Lists for the set of photometry plots and set of astrometry plots selected in plot checkbox
    selected_phot_plots, selected_ast_plots = param.List(), param.List()

    # Lists for the set of photometry traces and set of astrometry traces
    main_phot_keys, extra_phot_keys = param.List(), param.List()
    main_ast_keys, extra_ast_keys = param.List(), param.List()

    # Defining traces
    phot_traces = {
        'non_gp': traces.Genrl_Phot(
            group_name = 'Photometry',
            zorder = 100, show_legend = False,
            pri_clr = 'red', sec_clr = 'rgb(255, 77, 77)', 
            time_width = 2, full_width  = 1.5, marker_size = 10
        ),
        
        'gp_prior': traces.Genrl_Phot(
            group_name = 'GP Prior Mean',
            zorder = 90, show_legend = True,
            pri_clr = 'orange', sec_clr = 'rgba(255, 193, 77, 0.8)',
            time_width = 2, full_width  = 1.5, marker_size = 10
        ),
        
        'gp_predict': traces.Genrl_Phot(
            group_name = 'GP Predictive Mean', 
            zorder = 100, show_legend = True,
            pri_clr = 'red', sec_clr = 'rgba(255, 77, 77, 0.9)',
            time_width = 1.4, full_width  = 0.9, marker_size = 10, 
            full_dash_style = 'solid'
        ),
        
        'gp_samps': traces.Phot_GP_Samps(
            group_name = 'GP Prior Samples',
            time_width = 0.3
        )
    }

    ast_traces = {
        'unres_len': traces.Ast_Unres(
            group_name = 'Unresolved, Lensed Source(s)',
            zorder = 90,
            pri_clr = 'red', sec_clr = 'rgb(255, 77, 77)', 
            time_width = 1.5, full_width  = 1, marker_size = 8
        ),
        'unres_unlen': traces.Ast_Unres(
            group_name = 'Unresolved, Unlensed Source(s)',
            zorder = 80,
            pri_clr = 'orange', sec_clr = 'rgb(255, 193, 77)', 
            time_width = 1.5, full_width  = 1, marker_size = 8
        ),
        
        'ps_res_len': traces.Ast_PS_ResLensed(
            group_name = 'Resolved, Lensed Source Images',
            pri_clr = 'yellow',
            time_width = 1.2, marker_size = 6
        ),
        
        'bs_res_unlen_pri': traces.Ast_BS_ResUnlensed(
            src_idx = 0, group_name = 'Resolved, Unlensed Primary Source',
            zorder = 70,
            pri_clr = 'rgb(0, 134, 149)', sec_clr = 'rgb(0, 184, 204)', 
            time_width = 2, full_width  = 1.5, marker_size = 8
        ),
        'bs_res_unlen_sec': traces.Ast_BS_ResUnlensed(
            src_idx = 1, group_name = 'Resolved, Unlensed Secondary Source',
            zorder = 70,
            pri_clr = 'rgb(40, 121, 62)', sec_clr = 'rgb(51, 153, 78)', 
            time_width = 2, full_width  = 1.5, marker_size = 8
        ),
        
        'bs_res_len_pri': traces.Ast_BS_ResLensed(
            src_idx = 0, group_name = 'Resolved, Lensed Primary Source',
            pri_clr = 'rgb(128, 242, 255)',
            time_width = 1.2, marker_size = 6
        ),
        'bs_res_len_sec': traces.Ast_BS_ResLensed(
            src_idx = 1, group_name = 'Resolved, Lensed Secondary Source',
            pri_clr = 'rgb(0, 204, 150)',
            time_width = 1.2, marker_size = 6
        ),
        
        'lens': traces.Ast_Lens(
            group_name = 'Lens(es)',
            zorder = 100,
            pri_clr = 'rgb(148, 52, 110)', sec_clr = 'rgb(189, 66, 140)',
            time_width = 2, full_width  = 1.5, marker_size = 10
        )
    }

    # Sets for what keys have a time trace, a full trace, or a time marker
    time_trace_keys = {'non_gp', 'gp_prior', 'gp_predict', 'gp_samps',
                       'unres_len', 'unres_unlen', 
                       'ps_res_len',
                       'bs_res_unlen_pri', 'bs_res_unlen_sec', 'bs_res_len_pri', 'bs_res_len_sec',
                       'lens'}
    full_trace_keys = {'non_gp', 'gp_prior', 'gp_predict',
                       'unres_len', 'unres_unlen', 
                       'bs_res_unlen_pri', 'bs_res_unlen_sec', 
                       'lens'}
    marker_keys = {'non_gp', 'gp_prior', 'gp_predict',
                   'unres_len', 'unres_unlen', 
                   'ps_res_len',
                   'bs_res_unlen_pri', 'bs_res_unlen_sec', 'bs_res_len_pri', 'bs_res_len_sec',
                   'lens'}
    
    ########################
    # General Methods
    ######################## 
    def __init__(self, **params):
        # Trace Update functions for astrometry traces that are in ast_checkbox
        self.extra_ast_fns = {
            'ps_res_len': self._update_ps_res_len,
            'bs_res_unlen': self._update_bs_res_unlen,
            'bs_res_len_pri': self._update_bs_res_len,
            'bs_res_len_sec': self._update_bs_res_len,
            'lens': self._update_lens
        }
            
        # Plot row layout
        self.phot_pane = pn.pane.Plotly(config = self.get_plot_configs('photometry'),
                                        sizing_mode = 'stretch_height',
                                        visible = False,
                                        styles = constants.BASE_PLOT_STYLE)

        self.radec_pane = pn.pane.Plotly(config = self.get_plot_configs('ra_dec_astrometry'),
                                         sizing_mode = 'stretch_height',
                                         visible = False,
                                         styles = constants.BASE_PLOT_STYLE)
        
        self.ra_pane = pn.pane.Plotly(config = self.get_plot_configs('ra_astrometry'),
                                      sizing_mode = 'stretch_height',
                                      visible = False,
                                      styles = constants.BASE_PLOT_STYLE)
        
        self.dec_pane = pn.pane.Plotly(config = self.get_plot_configs('dec_astrometry'),
                                       sizing_mode = 'stretch_height',
                                       visible = False,
                                       styles = constants.BASE_PLOT_STYLE)
        
        self.plot_panes = {
            'phot': self.phot_pane, 
            'ast_radec': self.radec_pane, 
            'ast_ra': self.ra_pane, 
            'ast_dec': self.dec_pane
        }

        self.plot_layout = pn.FlexBox(objects = list(self.plot_panes.values()),
                                      flex_wrap = 'nowrap',
                                      gap = f'{2 * (50 - constants.PLOT_WIDTH)}%',
                                      styles = {'height':'65%', 'width':'100%',
                                                'overflow':'scroll'})

        # Set up initial figure formats
        self.init_figs = {
            'phot': go.Figure(),
            'ast_radec': go.Figure(),
            'ast_ra': go.Figure(),
            'ast_dec': go.Figure()
        }
        self.set_init_figs()

        # Initially empty figures for stylistic purposes (not really necessary)
        self.set_blank_figs()

        # Define slider-related dependencies
            # This is only used because @pn.depends with dictionary values doesn't work well
        super().__init__(**params)
        self.settings_info.param_sliders['Num_pts'].param.watch(self._update_mod_components, 'value')

        self.settings_info.param_sliders['Num_samps'].param.watch(self._update_gp_samps, 'value')
        self.settings_info.param_sliders['Num_samps'].param.watch(self._update_phot_plots, 'value')

        self.settings_info.param_sliders['Time'].param.watch(self._update_phot_plots, 'value')
        self.settings_info.param_sliders['Time'].param.watch(self._update_ast_plots, 'value')


    def get_plot_configs(self, plot_name):
        plot_configs = {
            'toImageButtonOptions': {'filename': plot_name, 'scale': 5}, 
            'displayModeBar': True, 'displaylogo': False,
            'modeBarButtonsToRemove': ['autoScale', 'lasso', 'select']
            }
        return plot_configs 
    
    def set_init_figs(self):
        for key in self.init_figs.keys():
            self.init_figs[key].update_xaxes(
                title = constants.FORMAT_DICT[key][1][0],
                title_font_size = constants.FONTSIZES['plot_axes_labels'],
                ticks = 'outside', tickformat = '000',
                color = 'white',
                gridcolor = constants.CLRS['gridline'], zeroline = False
            )

            self.init_figs[key].update_yaxes(
                title = constants.FORMAT_DICT[key][1][1],
                title_font_size = constants.FONTSIZES['plot_axes_labels'],
                ticks = 'outside', tickformat = '000',
                color = 'white',
                gridcolor = constants.CLRS['gridline'], zeroline = False
            )

            self.init_figs[key].update_layout(
                title = dict(text = constants.FORMAT_DICT[key][0], y = 0.99,
                             font = dict(color = 'white', 
                                         size = constants.FONTSIZES['plot_title'])),
                plot_bgcolor = constants.CLRS['secondary'], 
                paper_bgcolor = constants.CLRS['secondary'],
                font_size = constants.FONTSIZES['plot_axes_ticks'],
                legend = dict(font_color = 'white',
                              grouptitlefont_color = 'white'),
                margin = dict(l = 0, r = 0, t = 30, b = 0)
            )
        
        # Reverse y-axis for photometry magnitude
        self.init_figs['phot'].update_yaxes(autorange = 'reversed')

    def set_blank_figs(self):
        blank_fig = go.Figure(layout = dict(plot_bgcolor = constants.CLRS['secondary'],
                                            paper_bgcolor = constants.CLRS['secondary']))
        blank_fig.update_xaxes(showgrid = False, zeroline = False, showticklabels = False)
        blank_fig.update_yaxes(showgrid = False, zeroline = False, showticklabels = False)
        for pane in self.plot_panes.values():
            pane.object = blank_fig

    @pn.depends('settings_info.dashboard_checkbox.value', watch = True)
    def _update_selected_plots(self):
        self.selected_phot_plots = list({'phot'} & set(self.settings_info.dashboard_checkbox.value))
        self.selected_ast_plots = list({'ast_radec', 'ast_ra', 'ast_dec'} & set(self.settings_info.dashboard_checkbox.value))

    @pn.depends('settings_info.trigger_param_change', watch = True)
    def _update_mod_components(self, *event):
        # Note: '*event' is needed for 'Num_pts' watcher
    
        # Note: lock needed to guard against Num_pts slider reset because trigger_param_change also triggers the update
            # See chain: update_table_and_checks => update_sliders => update_param_values in SettingsTabs class
        if self.settings_info.lock_trigger == False:
            self.time = np.linspace(start = self.settings_info.param_sliders['Time'].start, 
                                    stop = self.settings_info.param_sliders['Time'].end, 
                                    num = self.settings_info.param_sliders['Num_pts'].value)
            
            # Check for bad parameter combination (e.g. dL > dS)  
            try:
                # Set model
                self.mod = getattr(model, self.paramztn_info.selected_paramztn)(**self.settings_info.param_values)

                # Update photometry
                # Note: there are currently no extra photometry traces from phot_checkbox
                    # I'm including GP samples as a main trace here, despite its dependency on 'Num_samps'
                self._update_main_phot_traces()
                self._update_phot_plots()

                # Update astrometry
                self._update_main_ast_traces()
                self._update_extra_ast_traces()
                self._update_ast_plots()

                # Check if 'Num_pts' slider is disabled
                    # Note: this assumes that the 'Num_pts' slider will never cause an exception, which should be true
                if self.settings_info.param_sliders['Num_pts'].disabled == True:
                    self.settings_info.set_slider_errored_layout(undo = True)

            except:
                self.set_blank_figs()
                self.settings_info.set_slider_errored_layout(undo = False)

    ########################
    # Photometry Methods
    ######################## 
    @pn.depends('selected_phot_plots', watch = True)
    def _update_main_phot_traces(self):
        # Check if photometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_phot_plots) != 0) and (self.settings_info.lock_trigger == False):
            
            # Check for GP
            if 'GP' in self.paramztn_info.selected_paramztn:
                selected_params = self.paramztn_info.selected_params
                param_values = self.settings_info.param_values

                cel_mod = model.Celerite_GP_Model(self.mod, 0)
                    
                # Matern-3/2 parameters
                log_sig = param_values['gp_log_sigma']

                if 'gp_rho' in selected_params:
                    log_rho = np.log(param_values['gp_rho'])
                elif 'gp_log_rho' in selected_params:
                    log_rho = param_values['gp_log_rho']

                # DDSHO parameters
                gp_log_Q = np.log(2**-0.5)
                log_omega0 = param_values['gp_log_omega0']

                if 'gp_log_S0'in selected_params:
                    log_S0 = param_values['gp_log_S0']
                elif 'gp_log_omega04_S0' in selected_params:
                    log_S0 = param_values['gp_log_omega04_S0'] - (4 * log_omega0)    
                elif 'gp_log_omega0_S0' in selected_params:
                    log_S0 = param_values['gp_log_omega0_S0'] - log_omega0
    
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

                gp = celerite.GP(kernel, mean = cel_mod, fit_mean = True)
                gp.compute(self.time, mag_obs_err)
                self.gp = gp

                # Get prior mean. Note that mag_obs = mod.get_photometry(time) for a nonGP, PSPL model
                self.phot_traces['gp_prior'].update_traces(mag_obs, self.time)

                # Get predictive mean
                mag_obs_corr = gp.sample(size = 1)[0]
                gp_phot = gp.predict(mag_obs_corr, return_cov = False)
                self.phot_traces['gp_predict'].update_traces(gp_phot, self.time)

                # Get gp samples
                self._update_gp_samps()

                # Reset phot keys
                self.main_phot_keys = ['gp_prior', 'gp_predict', 'gp_samps']
            else:
                phot = self.mod.get_photometry(self.time)
                self.phot_traces['non_gp'].update_traces(phot, self.time)

                # Reset phot keys
                self.main_phot_keys = ['non_gp']

    def _update_gp_samps(self, *event):
        # Note: '*event' is needed for 'Num_samps' watcher

        # Check if photometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets and slider resets
        if (len(self.selected_phot_plots) != 0) and (self.settings_info.lock_trigger == False):
            num_samps = self.settings_info.param_sliders['Num_samps'].value
            samp_list = self.gp.sample(size = num_samps)
            self.phot_traces['gp_samps'].update_traces(samp_list = samp_list, num_samps = num_samps, time = self.time)

    @pn.depends('selected_phot_plots', 
                'settings_info.phot_checkbox.value', 'settings_info.genrl_plot_checkbox.value', watch = True)
    def _update_phot_plots(self, *event):
        # Note: '*event' is needed for 'Time' and 'Num_samps' watcher

        # Check if photometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_phot_plots) != 0) and (self.settings_info.lock_trigger == False):

            # Get times that are less than or equal to Time slider
            time_idx = np.where(self.time <= self.settings_info.param_sliders['Time'].value)[0]

            # Create photometry figure
            phot_fig = go.Figure(self.init_figs['phot'])

            selected_trace_keys = set(self.main_phot_keys + self.extra_phot_keys)

            # Get all keys with a time trace and plot them
            selected_time_keys = selected_trace_keys & self.time_trace_keys
            all_phot = []
            
            for key in selected_time_keys:
                self.phot_traces[key].plot_time(fig = phot_fig, time_idx = time_idx)
                all_phot += self.phot_traces[key].get_phot_list()

            # Get all keys with a full trace and plot them
            if 'full_trace' in self.settings_info.genrl_plot_checkbox.value:
                selected_full_keys = selected_trace_keys & self.full_trace_keys

                for key in selected_full_keys:
                    self.phot_traces[key].plot_full(fig = phot_fig)

            # Get all keys with a marker trace and plot them
            if 'marker' in self.settings_info.genrl_plot_checkbox.value:
                selected_marker_keys = selected_trace_keys & self.marker_keys

                for key in selected_marker_keys:
                    self.phot_traces[key].plot_marker(fig = phot_fig, marker_idx = time_idx[-1])
            
            # Set up traces to fix axis limits
            min_time, max_time = np.nanmin(self.time), np.nanmax(self.time)
            min_phot, max_phot = np.nanmin(all_phot), np.nanmax(all_phot)

            traces.add_limit_trace(
                fig = phot_fig, 
                x_limits = [min_time, max_time],
                y_limits = [min_phot, max_phot]
            )

            # Update photometry pane with figure
            self.phot_pane.object = phot_fig

    ########################
    # Astrometry Methods
    ######################## 
    @pn.depends('selected_ast_plots', watch = True)
    def _update_main_ast_traces(self):
        # Check if astrometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_ast_plots) != 0) and (self.settings_info.lock_trigger == False):
            selected_paramztn = self.paramztn_info.selected_paramztn
            if 'PL' in selected_paramztn:
                unres_len = self.mod.get_astrometry(self.time)
            elif 'BL' in selected_paramztn:
                self.image_arr, self.amp_arr = self.mod.get_all_arrays(self.time)
                unres_len = self.mod.get_astrometry(self.time, self.image_arr, self.amp_arr)

            self.ast_traces['unres_len'].update_traces(unres_len, self.time)

            unres_unlen = self.mod.get_astrometry_unlensed(self.time)
            self.ast_traces['unres_unlen'].update_traces(unres_unlen, self.time)

            # Reset ast keys
            self.main_ast_keys = ['unres_len', 'unres_unlen']

    @pn.depends('selected_ast_plots', 'settings_info.ast_checkbox.value', watch = True)
    def _update_extra_ast_traces(self):
        # Check if astrometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_ast_plots) != 0) and (self.settings_info.lock_trigger == False):
            self.extra_ast_keys = []
            for key in self.settings_info.ast_checkbox.value:
                self.extra_ast_keys.append(key)
                self.extra_ast_fns[key]()

            # separate 'bs_res_unlen' traces
            if 'bs_res_unlen' in self.extra_ast_keys:
                self.extra_ast_keys.remove('bs_res_unlen')
                self.extra_ast_keys += ['bs_res_unlen_pri', 'bs_res_unlen_sec']

    def _update_ps_res_len(self):
        ps_res_len = self.mod.get_resolved_astrometry(self.time)
        self.ast_traces['ps_res_len'].update_traces(ps_res_len, self.paramztn_info.selected_paramztn, self.time)

    def _update_bs_res_unlen(self):
        bs_res_unlen = self.mod.get_resolved_astrometry_unlensed(self.time)
        self.ast_traces['bs_res_unlen_pri'].update_traces(bs_res_unlen, self.time)
        self.ast_traces['bs_res_unlen_sec'].update_traces(bs_res_unlen, self.time)

    def _update_bs_res_len(self):
        # Check if 'res_bs_unlen_pri' or 'res_bs_unlen_sec' are already keys in extra_ast_keys
            # This is done to prevent cases where 'get_resolved_astrometry_unlensed' is ran twice
        if not {'bs_res_len_pri', 'bs_res_len_sec'} <= set(self.extra_ast_keys):
            selected_paramztn = self.paramztn_info.selected_paramztn

            if 'PL' in selected_paramztn:
                bs_res_len = self.mod.get_resolved_astrometry(self.time)
            elif 'BL' in selected_paramztn:
                bs_res_len = self.mod.get_resolved_astrometry(self.time, self.image_arr, self.amp_arr)
            
            self.ast_traces['bs_res_len_pri'].update_traces(bs_res_len, selected_paramztn ,self.time)
            self.ast_traces['bs_res_len_sec'].update_traces(bs_res_len, selected_paramztn, self.time)

    def _update_lens(self):
        selected_paramztn = self.paramztn_info.selected_paramztn

        if 'PL' in selected_paramztn:
            lens_ast = self.mod.get_lens_astrometry(self.time)
        elif 'BL' in selected_paramztn:
            lens_ast = self.mod.get_resolved_lens_astrometry(self.time)

        self.ast_traces['lens'].update_traces(lens_ast, selected_paramztn, self.time)

    @pn.depends('selected_ast_plots', 
                'settings_info.ast_checkbox.value', 'settings_info.genrl_plot_checkbox.value', watch = True)
    def _update_ast_plots(self, *event):
        # Note: '*event' is needed for 'Time' watcher

        # Check if astrometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_ast_plots) != 0) and (self.settings_info.lock_trigger == False):

            # Get times that are less than or equal to Time slider
            time_idx = np.where(self.time <= self.settings_info.param_sliders['Time'].value)[0]

            for plot_key in self.selected_ast_plots:

                # Create figure
                ast_fig = go.Figure(self.init_figs[plot_key])

                # Get all trace keys that are to be plotted
                selected_trace_keys = set(self.main_ast_keys + self.extra_ast_keys)

                # Get all keys with a time trace and plot them
                selected_time_keys = selected_trace_keys & self.time_trace_keys
                all_x, all_y = [], []

                for trace_key in selected_time_keys:
                    self.ast_traces[trace_key].plot_time(fig = ast_fig, plot_key = plot_key, time_idx = time_idx)
                    x_list, y_list = self.ast_traces[trace_key].get_xy_lists(plot_key = plot_key)
                    all_x += x_list
                    all_y += y_list

                # Get all keys with a full trace and plot them
                if 'full_trace' in self.settings_info.genrl_plot_checkbox.value:
                    selected_full_keys = selected_trace_keys & self.full_trace_keys

                    for trace_key in selected_full_keys:
                        self.ast_traces[trace_key].plot_full(fig = ast_fig, plot_key = plot_key)

                # Get all keys with a marker trace and plot them
                if 'marker' in self.settings_info.genrl_plot_checkbox.value:
                    selected_marker_keys = selected_trace_keys & self.marker_keys

                    for trace_key in selected_marker_keys:
                        self.ast_traces[trace_key].plot_marker(fig = ast_fig, plot_key = plot_key, marker_idx = time_idx[-1])

                # Set up traces to fix axis limits
                min_x, max_x = np.nanmin(all_x), np.nanmax(all_x)
                min_y, max_y = np.nanmin(all_y), np.nanmax(all_y)

                traces.add_limit_trace(
                    fig = ast_fig, 
                    x_limits = [min_x, max_x],
                    y_limits = [min_y, max_y]
                )

                # Update astrometry pane with figure
                self.plot_panes[plot_key].object = ast_fig

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
        self.settings_tabs = SettingsTabs(paramztn_info = self.paramztn_info)
        self.param_summary = ParamSummary(paramztn_info = self.paramztn_info, settings_info = self.settings_tabs)
        self.param_row = pn.FlexBox(self.param_summary, 
                                    self.settings_tabs, 
                                    gap = '0.5%',
                                    flex_wrap = 'nowrap',
                                    styles = {'height':'35%'})
        
        # Plot section
        self.plot_row = PlotRow(paramztn_info = self.paramztn_info, settings_info = self.settings_tabs)
        
        # Entire dashboard layout
        self.db_components = {
            'summary': self.param_summary.summary_layout,
            'phot': self.plot_row.phot_pane,
            'ast_radec': self.plot_row.radec_pane,
            'ast_ra': self.plot_row.ra_pane,
            'ast_dec': self.plot_row.dec_pane
        }

        # a variable to store dashboard plot component if there is only a single plot
        self.current_single_plot = None

        self.dashboard_layout = pn.FlexBox(self.plot_row,
                                           self.param_row,
                                           flex_direction = 'column',
                                           visible = False,
                                           styles = {'margin-left':'1%',
                                                     'margin-right':'1%',
                                                     'min-height':'500px',
                                                     'max-height':'1500px',
                                                     'height':'100vh',
                                                     'width': '98%',
                                                     'border':'solid white 0.02rem',
                                                     'border-top':'none', 'border-bottom':'none'})
        
        # Add dependency of checkbox and layout
        # Note: this is needed because 'settings_tabs' is a class that uses a required input class
        self.settings_tabs.dashboard_checkbox.param.watch(self._update_layout, 'value')
        self.settings_tabs.error_msg.param.watch(self._range_errored_layout, 'object')
        
    @pn.depends('paramztn_info.selected_paramztn', watch = True)
    def _hide_show(self):
        if self.paramztn_info.selected_paramztn == None:
            self.dashboard_layout.visible = False
            self.plot_row.set_blank_figs()
            
        else:
            self.dashboard_layout.visible = True
            self.settings_tabs.update_table_and_checks()
            self.settings_tabs.update_sliders()
            
    def _update_layout(self, *event):
        # Set settings_tabs to its unerrored layout
        self.settings_tabs.set_base_layout()

        unchecked_components = set(self.db_components.keys()) - set(self.settings_tabs.dashboard_checkbox.value)
        checked_plots = list(set(self.settings_tabs.dashboard_checkbox.value) - {'summary'})

        for key in self.settings_tabs.dashboard_checkbox.value:
            self.db_components[key].visible = True

        for key in unchecked_components:
            self.db_components[key].visible = False

        if len(checked_plots) > 0:
            self.param_row.styles = {'height':'35%'}
            self.plot_row.plot_layout.visible = True

            # Expand plot if there is only a single plot
            if len(checked_plots) == 1:
                self.current_single_plot = self.db_components[checked_plots[0]]
                self.current_single_plot.styles = constants.SINGLE_PLOT_STYLE

            elif self.current_single_plot != None:
                self.current_single_plot.styles = constants.BASE_PLOT_STYLE

        # Hide plot row and expand param row if no plots are checked
        else:
            self.param_row.styles = {'height':'100%'}
            self.plot_row.plot_layout.visible = False
        
    def _range_errored_layout(self, *event):
        if self.settings_tabs.error_msg.object == None:
            self._update_layout()
            
        else:
            self.settings_tabs.set_range_errored_layout()
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
                                       styles = {'font-size':constants.FONTSIZES['page_title'], 
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