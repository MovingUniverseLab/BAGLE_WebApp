################################################
# Packages
################################################
import re
import sys

import numpy as np

import panel as pn
from panel.viewable import Viewer
from panel.theme import Material
import param

from app_utils import constants
from app_components import paramztn_select


################################################
# Dashboard - Parameter Tabs
################################################
class SettingsTabs(Viewer):
    # To be instantiated classes (required inputs)
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    
    # Parameters to prevent unwanted updates or trigger updates
        # It might be better to make lock_trigger into a dictionary to store locks for different components
        # Currently not needed, but this could separate Time slider lock and checkbox locks
    lock_trigger, trigger_param_change = param.Boolean(), param.Boolean()
    
    # Parameter to trigger error layouts
    error_trigger = param.Boolean()

    # Parameter to indicate whether sliders are throttled (e.g. when we have a BL model)
    throttled = param.Boolean()

    # Current parameter being changes. The default 'Time' is just a placeholder
    current_param_change = param.String(default = 'Time')

    # Dictionary for model parameter values
    mod_param_values = param.Dict(default = {})
    
    # Pandas dataframe for parameter values
    param_df = param.DataFrame()
    
    # Checkbox for dashboard panes
    db_options_dict = {
        'Phot': {'Photometry': 'phot', 
                'Parameter Summary': 'summary',
                'Display Data Code': 'code'},

        'Astrom': {'RA vs. Dec (Astrometry)':'ast_radec', 
                'RA vs. Time (Astrometry)':'ast_ra', 
                'Dec vs. Time (Astrometry)':'ast_dec', 
                'Parameter Summary':'summary',
                'Display Data Code': 'code'},

        'PhotAstrom': {'Photometry':'phot', 
                    'RA vs. Dec (Astrometry)':'ast_radec', 
                    'RA vs. Time (Astrometry)':'ast_ra', 
                    'Dec vs. Time (Astrometry)':'ast_dec', 
                    'Parameter Summary':'summary',
                    'Display Data Code': 'code'}
    }
    
    def __init__(self, **params):
        # Dictionary to store all sliders and watchers. 
            # Note: This is needed so that we don't always create new sliders and lag the page from memory leaks.
        self.param_sliders, self.slider_watchers = {}, {}

        # Time and number of point sliders (for all models)
        self.param_sliders['Time'] = pn.widgets.FloatSlider(
            name = 'Time [MJD]',
            format = '1[.]000',
            margin = (10, 12, -2, 18),
            design = Material,
            stylesheets = [constants.BASE_SLIDER_STYLE]
        )

        self.param_sliders['Num_pts'] = pn.widgets.IntSlider(
            name = 'Number of Points (Trace Resolution)',
            start = 1000, value = 3500, end = 25000, step = 100,
            format = '1[.]000',
            margin = (10, 12, -2, 18),
            design = Material,
            stylesheets = [constants.BASE_SLIDER_STYLE]
        )

        # Slider used for GP prior samples
        self.param_sliders['Num_samps'] = pn.widgets.IntSlider(
            name = 'Number of GP Samples',
            start = 0, value = 3, end = 10, step = 1,
            visible = False,
            format = '1[.]000',
            margin = (10, 0, -2, 18),
            design = Material,
            stylesheets = [constants.BASE_SLIDER_STYLE]
        )
    
        # Layout for model-dependent sliders
        self.mod_sliders = pn.FlexBox(
            flex_wrap = 'wrap', 
            styles = {'padding-bottom':'0.5rem', 
            'max-height':'fit-content'}
        )
    
        # Layout for sliders that are present in all models
        self.const_sliders = pn.FlexBox(
            self.param_sliders['Time'], 
            self.param_sliders['Num_pts'],
            flex_wrap = 'wrap'
        )
    
        self.slider_note = pn.pane.HTML(
            object = f'''
                <div style="font-size:{constants.FONTSIZES['tabs_txt']};font-family:{constants.HTML_FONTFAMILY}">
                    <span><b>Note:</b> Trace resolution slider is always throttled.</span>
                    </br>
                    <span><b>Note:</b> Parameter sliders are throttled for binary-lens models and when the number of points exceed 10000.</span>
                </div>
            ''',
            styles = {'color':'rgb(204, 204, 204)', 'margin-bottom': '0', 'text-align':'start', 'width':'90%'}
        )

        # Layout for all sliders
        self.sliders_content = [
            self.slider_note, 
            pn.layout.Divider(),
            self.const_sliders,
            self.param_sliders['Num_samps'],
            pn.layout.Divider(margin = (10, 0, 0, 0)),
            self.mod_sliders
        ]

        self.sliders_layout = pn.Column(
            objects = self.sliders_content,
            name = 'Parameter Sliders',
            styles = {'overflow':'scroll', 
                        'height':'100%', 
                        'border-top':'white solid 0.08rem'}
        )

        # Table for slider range settings
        self.range_table = pn.widgets.Tabulator(
            name = 'Slider Settings',
            text_align = 'left', layout = 'fit_columns',
            editors = {'Units': None}, 
            sizing_mode = 'stretch_both',
            stylesheets = [constants.TABLTR_STYLE]
        )
    
        # HTML message for errored slider range settings
        self.error_msg = pn.pane.HTML(object = None, name = 'ERRORED SLIDERS')
    
        self.dashboard_settings_header = pn.pane.HTML(
            object = f'''
                <div style="text-align:center">
                    <span style="font-size:{constants.FONTSIZES['checkbox_title']};font-family:{constants.HTML_FONTFAMILY};color:white">
                        <u><b>Dashboard Layout</b></u>
                    </span>
                    </br>
                    <span style="font-size:{constants.FONTSIZES['checkbox_txt']};font-family:{constants.HTML_FONTFAMILY};color:{constants.CLRS['tab_note']}">
                        <b>Note:</b> For 2+ (with code displayed) or 3+ plots, scroll right.
                    </span>
                </div>
            ''',
            margin = 0
        )

        self.dashboard_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
        self.dashboard_settings = pn.Column(
            self.dashboard_settings_header, 
            self.dashboard_checkbox, 
            styles = {'margin':'0.8rem'}
        )
    
        # Checkbox for general plot settings
        self.genrl_plot_settings_header = pn.pane.HTML(
            object = f'''
                <span style="font-size:{constants.FONTSIZES['checkbox_title']};font-family:{constants.HTML_FONTFAMILY};color:white">
                    <u><b>General Plot Settings</b></u>
                </span>
            ''',
            margin = 0
        )
        self.genrl_plot_checkbox = pn.widgets.CheckBoxGroup(options = {'Show Time Markers': 'marker', 'Show Full Traces': 'full_trace'},
                                                            inline = False, align = 'center')
        self.genrl_plot_settings = pn.Column(
            self.genrl_plot_settings_header, 
            self.genrl_plot_checkbox, 
            styles = {'margin':'0.8rem'}
        )
    
        # Checkbox for photometry settings (currently no options to add)
        self.phot_settings_header = pn.pane.HTML(
            object = f'''
                <span style="font-size:{constants.FONTSIZES['checkbox_title']};font-family:{constants.HTML_FONTFAMILY};color:white">
                    <u><b>Photometry Plot Settings</b></u>
                </span>
            ''',
            margin = 0
        )
        self.phot_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
        self.phot_settings = pn.Column(
            self.phot_settings_header, 
            self.phot_checkbox, 
            visible = False,
            styles = {'margin':'0.8rem'}
        )
    
        # Checkbox for astrometry settings
        self.ast_settings_header = pn.pane.HTML(
            object = f'''
                <div style="text-align:center">
                    <span style="font-size:{constants.FONTSIZES['checkbox_title']};font-family:{constants.HTML_FONTFAMILY};color:white">
                        <u><b>Astrometry Plot Settings</b></u>
                    </span>
                    </br>
                    <span style="font-size:{constants.FONTSIZES['checkbox_txt']};font-family:{constants.HTML_FONTFAMILY};color:{constants.CLRS['tab_note']}">
                        <b>Note:</b> Lens may not be visible without Time Marker.
                    </span>
                </div>
            ''',
            margin = 0
        )

        self.ast_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
        self.ast_settings = pn.Column(
            self.ast_settings_header, 
            self.ast_checkbox, 
            visible = False,
            styles = {'margin':'0.8rem'}
        )
    
        self.performance_note = pn.pane.HTML(
            object = f'''
                <span style="font-size:{constants.FONTSIZES['tabs_txt']};font-family:{constants.HTML_FONTFAMILY}">
                    <b>Note:</b> For best performance, it's recommended to either reduce the number of traces or the number of figures while using sliders.
                </span>
            ''',
            styles = {'color':constants.CLRS['tab_note'], 'margin-bottom':'0', 'width':'95%'},
            align = 'center'
        )

        # Layout for settings tab
        self.all_settings = pn.FlexBox(
            self.dashboard_settings, 
            self.genrl_plot_settings, 
            self.phot_settings,
            self.ast_settings,
            justify_content = 'center',
        )
            
        self.settings_layout = pn.Column(
            self.performance_note,
            pn.layout.Divider(),
            self.all_settings,
            name = 'Other Settings',
            styles = {'overflow':'scroll'}
        )

        # Links tab
        self.github_links = pn.pane.HTML(
            object = f'''
                <span style="font-size:{constants.FONTSIZES['header']}">
                    <b><u>GitHub Repositories:</u></b>
                </span>
                </br>
                <span style="font-size:{constants.FONTSIZES['tabs_txt']};color:rgb(204, 204, 204)">
                    Please feel free to send any feedback through the BAGLE Web App repo. Thank you!
                </span>
                </br>
                <ul style="font-size:{constants.FONTSIZES['summary_txt']}">
                    <li><a href="https://github.com/MovingUniverseLab/BAGLE_WebApp" target="_blank">BAGLE Web Application</a></li>
                    <li><a href="https://github.com/MovingUniverseLab/BAGLE_Microlensing/tree/dev" target="_blank">BAGLE Microlensing (Dev Branch)</a></li>
                </ul>
            ''',
            name = 'Links', styles = {'color':'white', 'width':'95%', 'font-family':constants.HTML_FONTFAMILY}
        )

        # Layout for entire tab section
        self.tabs_layout = pn.Tabs(
            self.sliders_layout,
            self.range_table, 
            self.settings_layout, 
            self.github_links,
            styles = {'border':'white solid 0.08rem', 'background':constants.CLRS['secondary']}
        )
    

        super().__init__(**params)
        # set dependencies and on-edit functions
        self.range_table.on_edit(self._update_param_change)
        self.param_sliders['Num_pts'].param.watch(self._change_slider_throttle, 'value_throttled')
        self.param_sliders['Time'].param.watch(self._update_param_values, 'value')

    def set_base_layout(self):
        for object in self.tabs_layout.objects:
            object.visible = True

        self.tabs_layout.stylesheets = [constants.BASE_TABS_STYLE]

    def set_slider_errored_layout(self, undo):
        event_slider = self.param_sliders[self.current_param_change]

        if undo == False:
            self.tabs_layout.stylesheets = [constants.ERRORED_TABS_STYLE]
            self.tabs_layout.active = 0

            for param in self.param_sliders.keys():
                self.param_sliders[param].disabled = True
            event_slider.param.update(disabled = False, stylesheets = [constants.ERRORED_SLIDER_STYLE])

            self.settings_layout.visible, self.range_table.visible = False, False
            self.error_trigger = not self.error_trigger

        else:
            self.set_base_layout()
            event_slider.stylesheets = [constants.BASE_SLIDER_STYLE]

            for param in self.param_sliders.keys():
                self.param_sliders[param].disabled = False

    @pn.depends('error_msg.object', watch = True)
    def set_range_errored_layout(self):
        if self.error_msg.object == None:
            self.set_base_layout()
            self.sliders_layout.objects = self.sliders_content

        else:
            self.tabs_layout.stylesheets = [constants.ERRORED_TABS_STYLE]
            self.sliders_layout.objects = [self.error_msg]

            self.tabs_layout.active = 0
            self.settings_layout.visible = False
            self.error_trigger = not self.error_trigger

    def _check_genrl_errors(self, param, default_val, min_val, max_val, step_val):
        error_html = ''''''
        if np.any(np.isnan([default_val, min_val, max_val, step_val])):
            error_html += '''<li>Range inputs must be a number.</li>'''     
        if (min_val >= max_val):
            error_html += '''<li>The minimum value must be smaller than the maximum value.</li>'''
        elif ((default_val < min_val) or (default_val > max_val)):
            error_html += '''<li>The default value is not inside the range.</li>'''
        if (step_val > (abs(max_val - min_val))):
            error_html += '''<li>The step size cannot be larger than the range size.</li>'''

        # Make error message and exit if error exists
        if error_html != '''''':
            error_param = f'''<span style="color:rgb(179, 0, 89);font-weight:bold">{param}</span>'''
            self.error_msg.object = f'''
                <span style="color:red; font-size:{constants.FONTSIZES['error_title']};font-family:{constants.HTML_FONTFAMILY}">
                    Errors in {error_param} Slider:
                </span>
                <ul style="color:white; font-size:{constants.FONTSIZES['error_txt']};font-family:{constants.HTML_FONTFAMILY}">
                    {error_html}
                </ul>
            '''
            
            # Force the function that called this function to exit
            sys.exit()

    def set_default_table_and_checkboxes(self):
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
            self.ast_settings.visible = True
        
        # Data type is photometry-only
        else:
            self.ast_settings.visible = False
        
        db_options = self.db_options_dict[mod_types['data']]
        db_value = list(set(db_options.values()) - {'ast_ra', 'ast_dec', 'code'})
        self.dashboard_checkbox.param.update(options = db_options, value = db_value)  
        self.genrl_plot_checkbox.param.update(value = ['marker', 'full_trace'])

        self.lock_trigger = False
        
        # Update range data frame
        idx_list = ['Time'] + self.paramztn_info.selected_params
        self.range_table.value = constants.DEFAULT_DF.loc[idx_list]

        # Reset parameter data frame
        self.param_df = constants.DEFAULT_DF.copy()

        # Reset tab to parameter sliders tab
        # The scroll of the parameter sliders tab bugs if it directly set with 'active'
            # For some reason setting 'active = 1' (or some other tab) first seems to fix this
        self.tabs_layout.active = 1
        self.tabs_layout.active = 0
        
    def _update_param_change(self, *event):
        self.current_param_change = self.range_table.value.index[event[0].row]
        self.update_sliders()
    
    def update_sliders(self):
        df = self.range_table.value
        selected_paramztn = self.paramztn_info.selected_paramztn
    
        # Note: Lock is needed because initial trace changes will be applied by the initialized param value dictionary (leads to 'trigger_param_change')
        self.lock_trigger = True

        if 'BL' in selected_paramztn:
            self.param_sliders['Num_pts'].param.update(value = 1000)
        else:
            self.param_sliders['Num_pts'].param.update(value = 3000)

        if 'GP' in selected_paramztn:
            self.param_sliders['Num_samps'].visible = True
            self.param_sliders['Num_samps'].param.update(value = 3)
        else:
            self.param_sliders['Num_samps'].visible = False

        # Create/Update model-related sliders
        for param in (['Time'] + self.paramztn_info.selected_params):
            units = df.loc[(param, 'Units')]
            current_val = df.loc[(param, 'Value')]
            min_val = df.loc[(param, 'Min')]
            max_val = df.loc[(param, 'Max')]
            step_val = df.loc[(param, 'Step')]

            # Check for errors
            try:
                self._check_genrl_errors(param, current_val, min_val, max_val, step_val)             
            except SystemExit:
                return
        
            # Update if slider already exists
            if param in self.param_sliders.keys():
                # Unwatch before updating to prevent multiple repeated watchers (memory leaks)
                # self.param_sliders[param].param.unwatch(self.slider_watchers[param])
                self.param_sliders[param].param.update(value = current_val, 
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
                                                                   value = current_val, 
                                                                   start = min_val, 
                                                                   end = max_val, 
                                                                   step = step_val,
                                                                   format = '1[.]000',
                                                                   margin = (10, 12, 10, 18),
                                                                   design = Material,
                                                                   stylesheets = [constants.BASE_SLIDER_STYLE])

        self.lock_trigger = False

        # Get relevant sliders and update slider_box
        self.mod_sliders.objects = [self.param_sliders[key] for key in self.paramztn_info.selected_params]

        # Initialize param values
        self._update_param_values()
        
        # Make watcher for slider
        # Note: throttled is enabled for binary lens because computation time is significantly longer
        self._change_slider_throttle()
        
        # Clear error message if no errors
        self.error_msg.object = None

    def _update_param_values(self, *event):
        # Note: the '*event' argument is used to set dependency on sliders

        # Lock needed to prevent excessive triggers when changing parameter sliders through parameterization or data table change
        if self.lock_trigger == False:
            
            # Function triggered by a slider
            if event != ():
                # Regex is used to get just the parameter name and not the unit
                param_name = re.match('[^\W\\[]*', event[0].obj.name).group()

                self.current_param_change = param_name

                # Change data frame value and range table
                self.param_df.loc[(param_name, 'Value')] = self.param_sliders[param_name].value

                idx_list = ['Time'] + self.paramztn_info.selected_params
                self.range_table.value = self.param_df.loc[idx_list]

            if (event == ()) or (self.current_param_change != 'Time'):
                # Update model parameter values
                temp_dict = {}
                for param in self.paramztn_info.selected_params:
                    # Note: 'phot_name' parameters should be inputed as an ndarray/list
                    if param in self.paramztn_info.selected_phot_params:
                        temp_dict[param] = np.array([self.param_sliders[param].value])
                    else:
                        temp_dict[param] = self.param_sliders[param].value

                self.mod_param_values = temp_dict

                # Note: a trigger is used because if self.mod_param_values doesn't change, updates don't occur
                # An example of this is changing slider 'Min/Max/Step', but not the slider value (i.e. 'Value')
                # I think this could also be resolved by using 'onlychanged = False' in the lower-level '.param.watch',
                    # instead of using '@pn.depends,' but that may make readability more confusing.
                    # See: https://param.holoviz.org/user_guide/Dependencies_and_Watchers.html#watchers
                self.trigger_param_change = not self.trigger_param_change
    
    def _change_slider_throttle(self, *event):
        # Lock needed to prevent overlap with changing data table
        # BL check needed to prevent undoing throttle for binary-lens models
        if self.lock_trigger == False:
            if (self.param_sliders['Num_pts'].value >= 10000) or ('BL' in self.paramztn_info.selected_paramztn):
                self.throttled = True
                dependency = 'value_throttled'
            else:
                self.throttled = False
                dependency = 'value'

            for param in self.paramztn_info.selected_params:
                # Unwatch before updating to prevent multiple repeated watchers (memory leaks)
                if param in self.slider_watchers:
                    self.param_sliders[param].param.unwatch(self.slider_watchers[param])

                self.slider_watchers[param] = self.param_sliders[param].param.watch(self._update_param_values, dependency)

    def __panel__(self):
        return self.tabs_layout

