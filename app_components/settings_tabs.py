################################################
# Packages
################################################
import re
import sys

import numpy as np

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import constants, styles
from app_components import paramztn_select


################################################
# Dashboard - Parameter Tabs
################################################
# This is a class to trigger error layouts
class ErrorBoolean(Viewer): 
    value = param.Boolean(default = False)

class SettingsTabs(Viewer):
    # To be instantiated classes (required inputs)
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)

    # Booleans to prevent unwanted updates or trigger updates
        # It might be better to make lock_trigger into a dictionary to store locks for different components
        # Currently not needed, but this could separate Time slider lock and checkbox locks
    lock_trigger, trigger_param_change = param.Boolean(), param.Boolean()

    # Parameter to indicate whether sliders are throttled (e.g. when we have a BL model)
    throttled = param.Boolean(default = False)

    # Current parameter being changes
    current_param_change = param.String()

    # Dictionary for model parameter values
    mod_param_values = param.Dict(default = {})
    
    # Checkbox for dashboard panes
    db_options_dict = {
        'Phot': {'Photometry': 'phot', 
                 'Parameter Summary': 'summary',
                 'Display Basic Data/Plot Code': 'code'},

        'Astrom': {'RA vs. Dec (Astrometry)':'ast_radec', 
                   'RA vs. Time (Astrometry)':'ast_ra', 
                   'Dec vs. Time (Astrometry)':'ast_dec', 
                   'Parameter Summary':'summary',
                   'Display Basic Data/Plot Code': 'code'},

        'PhotAstrom': {'Photometry':'phot', 
                       'RA vs. Dec (Astrometry)':'ast_radec', 
                       'RA vs. Time (Astrometry)':'ast_ra', 
                       'Dec vs. Time (Astrometry)':'ast_dec', 
                       'Parameter Summary':'summary',
                       'Display Basic Data/Plot Code': 'code'}
    }
    

    def __init__(self, **params):
        # Dictionary to track what caused errors and to trigger error layouts
        self.errored_state = {
            'params': ErrorBoolean(),
            'slider_settings': ErrorBoolean()
        }

        ###########################################
        # Tab 1 - Sliders
        ###########################################
        # Dictionary to store all sliders and watchers. 
            # Note: This is needed so that we don't always create new sliders and lag the page from memory leaks.
        self.param_sliders, self.slider_watchers = {}, {}

        # Time and number of point sliders (for all models)
        self.param_sliders['Time'] = pn.widgets.FloatSlider(
            name = 'Time [MJD]',
            format = '1[.]000',
            margin = (10, 12, -2, 18),
            design = styles.THEMES['slider_design'],
            stylesheets = [styles.BASE_SLIDER_STYLESHEET]
        )

        self.param_sliders['Num_pts'] = pn.widgets.IntSlider(
            name = 'Number of Points (Trace Resolution)',
            start = 1000, value = 3500, end = 25000, step = 100,
            format = '1[.]000',
            margin = (10, 12, -2, 18),
            design = styles.THEMES['slider_design'],
            stylesheets = [styles.BASE_SLIDER_STYLESHEET]
        )

        # Slider used for GP prior samples
        self.param_sliders['Num_samps'] = pn.widgets.IntSlider(
            name = 'Number of GP Samples',
            start = 0, value = 3, end = 10, step = 1,
            visible = False,
            format = '1[.]000',
            margin = (10, 0, -2, 18),
            design = styles.THEMES['slider_design'],
            stylesheets = [styles.BASE_SLIDER_STYLESHEET]
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

        # Note: the choice of approximating for the time slider was done so that we get a smoother, non-throttled, animation.
        self.slider_note = pn.pane.HTML(
            object = f'''
                <div style="font-size:{styles.FONTSIZES['tabs_txt']};font-family:{styles.HTML_FONTFAMILY}">
                    <p style = "margin-bottom:0.6rem; padding:0"><b>Note:</b> Trace resolution slider is always throttled.</p>
                    <p style = "margin-bottom:0.6rem; padding:0"><b>Note:</b> Time and Parameter sliders are throttled when the number of points exceed 10000. Additionally, Parameter sliders are also always throttled for binary-lens models.</p>
                    <p style = "margin-bottom:0.6rem; padding:0"><b>Note:</b> Changing the Time slider will only approximate the ending point of traces. For an accurate ending point, please change Time from the Parameter Values section.</p>
                </div>
            ''',
            styles = {'color':styles.CLRS['txt_secondary'],
                      'margin-bottom': '0', 
                      'text-align':'start', 
                      'width':'95%'},
            align = 'center'
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

        # This will be populated by 'set_default_tabs'
        self.sliders_layout = pn.Column(
            # objects = self.sliders_content,
            name = 'Parameter Sliders',
            styles = {'overflow-y':'scroll', 
                      'height':'100%', 
                      'border-top':f'{styles.CLRS["page_border"]} solid 0.08rem'}
        )


        ###########################################
        # Tab 2 & 3 - Parameter and Slider Tables
        ###########################################
        # Table for parameter values
        self.param_table = pn.widgets.Tabulator(
            name = 'Parameter Values',
            text_align = 'left', 
            layout = 'fit_columns',
            editors = {'Units': None}, 
            sizing_mode = 'stretch_both',
            stylesheets = [styles.TABLTR_STYLESHEET]
        )

        # Table for slider settings
        self.slider_table = pn.widgets.Tabulator(
            name = 'Slider Settings',
            text_align = 'left', 
            layout = 'fit_columns',
            editors = {'Units': None}, 
            sizing_mode = 'stretch_both',
            stylesheets = [styles.TABLTR_STYLESHEET]
        )

        # List containing all tables for easy disabling
        self.all_tables = [self.param_table, self.slider_table]

        # HTML message for errored slider range settings
        self.slider_error_msg = pn.pane.HTML(object = None, name = 'ERRORED SLIDERS')

    
        ###########################################
        # Tab 4 - Checkboxes
        ###########################################
        self.dashboard_settings_title = pn.pane.HTML(
            object = f'''
                <div style="text-align:center">
                    <span style="font-size:{styles.FONTSIZES['checkbox_title']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_primary']}">
                        <u><b>Dashboard Layout</b></u>
                    </span>
                    </br>
                    <span style="font-size:{styles.FONTSIZES['checkbox_txt']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_secondary']}">
                        <b>Note:</b> For 2+ (with code displayed) or 3+ plots, scroll right.
                    </span>
                </div>
            ''',
            margin = 0
        )
        self.dashboard_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
        self.dashboard_settings = pn.Column(
            self.dashboard_settings_title, 
            self.dashboard_checkbox, 
            styles = {'margin':'0.8rem'}
        )
    
        # Checkbox for general plot settings
        self.genrl_plot_settings_title = pn.pane.HTML(
            object = f'''
                <span style="font-size:{styles.FONTSIZES['checkbox_title']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_primary']}">
                    <u><b>General Plot Settings</b></u>
                </span>
            ''',
            margin = 0
        )
        self.genrl_plot_checkbox = pn.widgets.CheckBoxGroup(
            options = {'Show Title': 'title',
                       'Show Grid Lines': 'gridlines',
                       'Show Time Markers': 'marker', 
                       'Show Full Traces': 'full_trace',
                       'Show Color Panel': 'color'},
            inline = False, 
            align = 'center'
        )
        self.genrl_plot_settings = pn.Column(
            self.genrl_plot_settings_title, 
            self.genrl_plot_checkbox, 
            styles = {'margin':'0.8rem'}
        )
    
        # Checkbox for photometry settings (currently no options to add)
        self.phot_settings_title = pn.pane.HTML(
            object = f'''
                <span style="font-size:{styles.FONTSIZES['checkbox_title']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_primary']}">
                    <u><b>Photometry Plot Settings</b></u>
                </span>
            ''',
            margin = 0
        )
        self.phot_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
        self.phot_settings = pn.Column(
            self.phot_settings_title, 
            self.phot_checkbox, 
            visible = False,
            styles = {'margin':'0.8rem'}
        )
    
        # Checkbox for astrometry settings
        self.ast_settings_title = pn.pane.HTML(
            object = f'''
                <div style="text-align:center">
                    <span style="font-size:{styles.FONTSIZES['checkbox_title']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_primary']}">
                        <u><b>Astrometry Plot Settings</b></u>
                    </span>
                    </br>
                    <span style="font-size:{styles.FONTSIZES['checkbox_txt']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_secondary']}">
                        <b>Note:</b> Lens may not be visible without Time Marker.
                    </span>
                </div>
            ''',
            margin = 0
        )
        self.ast_checkbox = pn.widgets.CheckBoxGroup(inline = False, align = 'center')
        self.ast_settings = pn.Column(
            self.ast_settings_title, 
            self.ast_checkbox, 
            visible = False,
            styles = {'margin':'0.8rem'}
        )
        
        # A general note about page performance
        self.performance_note = pn.pane.HTML(
            object = f'''
                <p style="font-size:{styles.FONTSIZES['tabs_txt']};font-family:{styles.HTML_FONTFAMILY};margin-bottom:0.6rem; padding:0"">
                    <b>Note:</b> For best performance, it's recommended to either reduce the number of traces or the number of figures while using sliders.
                </p>
            ''',
            styles = {'color':styles.CLRS['txt_secondary'], 
                      'margin-bottom':'0', 
                      'width':'95%'},
            align = 'center'
        )

        # List containing all checkboxes for easy disabling
        self.all_checkboxes = [
            self.dashboard_checkbox,
            self.genrl_plot_checkbox,
            self.phot_checkbox,
            self.ast_checkbox
        ]

        # Layout for settings tab
        self.all_settings = pn.FlexBox(
            self.dashboard_settings, 
            self.genrl_plot_settings, 
            self.phot_settings,
            self.ast_settings,
            justify_content = 'center',
        )

        self.settings_content = [
            self.performance_note,
            pn.layout.Divider(),
            self.all_settings, 
        ]

        # This will be populated by 'set_default_tabs'
        self.settings_layout = pn.Column(
            name = 'Other Settings',
            styles = {'overflow-y':'scroll'}
        )


        ###########################################
        # Tab 5 - References/Citations
        ###########################################
        # Reference/citations tab
        self.refs_cites_html = pn.pane.HTML(
            object = f'''
                <span style="font-size:{styles.FONTSIZES['page_header']}">
                    <b><u>GitHub Repositories:</u></b>
                </span>
                </br>
                <span style="font-size:{styles.FONTSIZES['tabs_txt']};color:{styles.CLRS['txt_secondary']}">
                    Feel free to send any issues or feedback through the BAGLE Web App repo. Thank you!
                </span>
                </br>
                <ul style="font-size:{styles.FONTSIZES['summary_txt']}">
                    <li><a href="https://github.com/MovingUniverseLab/BAGLE_WebApp" target="_blank">BAGLE Web Application</a></li>
                    <li><a href="https://github.com/MovingUniverseLab/BAGLE_Microlensing/tree/dev" target="_blank">BAGLE Microlensing (Dev Branch)</a></li>
                </ul>
                <span style="font-size:{styles.FONTSIZES['page_header']}">
                    <b><u>About</u></b>
                </span>
                </br>
                <span style="font-size:{styles.FONTSIZES['tabs_txt']};color:{styles.CLRS['txt_secondary']}">
                    This web application was developed by Jeff Chen as part of a research project with UC Berkeley's Moving Universe Lab. 
                    It was designed to visually present the photometry/astrometry models from the <span style="font-weight:600">Bayesian Analysis of Gravitational Lensing Events (BAGLE)</span> Python package.
                    As such, if you use this resource, please make sure to cite <span style="font-weight:600">BAGLE</span>.
                </span>
                </br></br>
            ''',
            sizing_mode = 'stretch_width',
            align = 'center',
            styles = {'color':styles.CLRS['txt_primary'],
                      'font-family':styles.HTML_FONTFAMILY}
        )

        # This will be populated by 'set_default_tabs'
        self.refs_cites = pn.FlexBox(
            name = 'References/Citations', 
            sizing_mode = 'stretch_both', 
            styles = {'overflow-y':'scroll'}
        )


        ###########################################
        # Tabs Layout + Dependencies
        ###########################################
        self.tabs_layout = pn.Tabs(
            self.sliders_layout,
            self.param_table, 
            self.slider_table, 
            self.settings_layout, 
            self.refs_cites,
            styles = {'border':f'{styles.CLRS["page_border"]} solid 0.08rem', 
                      'background':styles.CLRS['page_secondary'], 
                      'overflow-x':'scroll', 'overflow-y':'hidden'}
        )

        super().__init__(**params)
        # set dependencies and on-edit functions
        self.param_sliders['Num_pts'].param.watch(self.set_mod_slider_throttle, 'value_throttled')
        self.param_sliders['Time'].param.watch(self._update_param_values, 'value')

        self.param_table.on_edit(self._update_param_table_change)
        self.slider_table.on_edit(self._update_sliders)


    def set_base_layout(self):
        for component in self.all_tables + self.all_checkboxes:
            component.disabled = False

        self.tabs_layout.stylesheets = [styles.BASE_TABS_STYLESHEET]
    

    def set_param_errored_layout(self, undo):
        if (undo == True) and (self.errored_state['params'].value == True):
            self.errored_state['params'].value = False
            self.set_base_layout()

            # event_slider = self.param_sliders[self.current_param_change]
            # event_slider.stylesheets = [styles.BASE_SLIDER_STYLESHEET]

            for param in self.param_sliders.keys():
                self.param_sliders[param].stylesheets = [styles.BASE_SLIDER_STYLESHEET]
                self.param_sliders[param].disabled = False

        elif undo == False:
            self.errored_state['params'].value = True

            self.tabs_layout.stylesheets = [styles.ERRORED_TABS_STYLESHEET]
            self.tabs_layout.active = 0

            # Disable all parameters except the one causing the error
            for param in self.param_sliders.keys():
                self.param_sliders[param].disabled = True

            event_slider = self.param_sliders[self.current_param_change]
            event_slider.param.update(disabled = False, stylesheets = [styles.ERRORED_SLIDER_STYLESHEET])

            # Disable all tables and checkboxes
            self.param_table.disabled = True
            for cb in self.all_checkboxes:
                cb.disabled = True


    def set_slider_errored_layout(self, undo): 
        if (undo == True) and (self.errored_state['slider_settings'].value == True):
            self.set_base_layout()
            self.sliders_layout.objects = self.sliders_content

            self.errored_state['slider_settings'].value = False

        elif undo == False:
            self.tabs_layout.stylesheets = [styles.ERRORED_TABS_STYLESHEET]
            self.sliders_layout.objects = [self.slider_error_msg]

            self.tabs_layout.active = 0

            # Note: slider table needs to remain enabled to fix error
            for cb in self.all_checkboxes:
                cb.disabled = True

            self.errored_state['slider_settings'].value = True


    def _check_errors(self, param, param_val, min_val, max_val, step_val):
        error_html = ''''''
        if np.any(np.isnan([param_val, min_val, max_val, step_val])):
            error_html += '''<li>All inputs must be numbers.</li>'''   

        if (min_val >= max_val):
            error_html += '''<li>The minimum value must be smaller than the maximum value.</li>'''
        elif (param_val < min_val) or (param_val > max_val):
            if param in ['Time']:
                error_html += '''<li>Value must be inside range.</li>'''

        if (step_val > (abs(max_val - min_val))):
            error_html += '''<li>The step size cannot be larger than the range size.</li>'''
        elif step_val <= 0:
            error_html += '''<li>The step size must be larger than zero.</li>'''

        # Make error message and exit if error exists
        if error_html != '''''':
            error_param = f'''<span style="color:{styles.CLRS['error_secondary']};font-weight:bold">{param}</span>'''
            self.slider_error_msg.object = f'''
                <span style="color:{styles.CLRS['error_primary']}; font-size:{styles.FONTSIZES['error_tabs_title']};font-family:{styles.HTML_FONTFAMILY}">
                    Errors in {error_param} Slider:
                </span>
                <ul style="color:{styles.CLRS['txt_primary']}; font-size:{styles.FONTSIZES['error_tabs_txt']};font-family:{styles.HTML_FONTFAMILY}">
                    {error_html}
                </ul>
            '''
            self.set_slider_errored_layout(undo = False)
            # Force the function that called this function to exit
            sys.exit()

        else:
            self.set_slider_errored_layout(undo = True)


    def set_default_tabs(self):
        self.throttled = False
        mod_types = self.paramztn_info.mod_info.type_dict
        self.set_base_layout()

        # Resetting scrolls for some tabs
            # I don't have access to JS, so as a work around, I clear the tabs and repopulate them
        self.sliders_layout.clear()
        self.sliders_layout.objects = self.sliders_content

        self.settings_layout.clear()
        self.settings_layout.objects = self.settings_content

        self.refs_cites.clear()
        self.refs_cites.objects = [self.refs_cites_html]
        
        # Update checkboxes
        # Note: Lock used to not trigger checkbox-related changes
            # This is needed because same changes will trigger through data frame update (leads to 'trigger_param_change')
        self.lock_trigger = True
        
        # # Will be used when more photometry options are added
        # if 'Phot' in mod_types['data']:
        #     self.phot_checkbox.param.update(value = [])
        #     self.phot_settings.visible = True
        # else:
        #     self.phot_settings.visible = False
        
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

        genrl_plot_value = set(self.genrl_plot_checkbox.options.values()) - {'full_trace', 'color'}
        self.genrl_plot_checkbox.param.update(value = list(genrl_plot_value))
        
        self.lock_trigger = False
        
        # Update tables
        idx_list = ['Time'] + self.paramztn_info.selected_params
        self.slider_table.value = constants.DEFAULT_SLIDER_DF.loc[idx_list]
        self.param_table.value = constants.DEFAULT_PARAM_DF.loc[idx_list]

        # Reset tab to parameter sliders tab
        self.tabs_layout.active = 0

        # Update sliders
        self._update_sliders()


    def _update_sliders(self, *event):
        param_df = self.param_table.value
        slider_df = self.slider_table.value
        selected_paramztn = self.paramztn_info.selected_paramztn
    
        # Note: Lock is needed because trace changes will be applied by the initialized param value dictionary (leads to 'trigger_param_change')
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
            units = param_df.loc[(param, 'Units')]
            current_val = param_df.loc[(param, 'Value')]
            min_val = slider_df.loc[(param, 'Min')]
            max_val = slider_df.loc[(param, 'Max')]
            step_val = slider_df.loc[(param, 'Step')]

            # Check for errors
            try:
                self._check_errors(param, current_val, min_val, max_val, step_val)             
            except SystemExit:
                return
        
            # Update if slider already exists
            if param in self.param_sliders.keys():
                self.param_sliders[param].param.update(
                    value = current_val, 
                    start = min_val, 
                    end = max_val,
                    step = step_val
                )

            # Create slider if it doesn't exist
            else:
                if units == None:
                    param_label = param
                else:
                    param_label = param + f' [{units}]'
                self.param_sliders[param] = pn.widgets.FloatSlider(
                    name = param_label,
                    value = current_val, 
                    start = min_val, 
                    end = max_val, 
                    step = step_val,
                    format = '1[.]000',
                    margin = (10, 12, 10, 18),
                    design = styles.THEMES['slider_design'],
                    stylesheets = [styles.BASE_SLIDER_STYLESHEET]
                )

        self.lock_trigger = False

        # Get relevant sliders and update slider_box
        self.mod_sliders.objects = [self.param_sliders[key] for key in self.paramztn_info.selected_params]

        # Initialize param values
        self._update_param_values()
        
        # Make watcher for slider
        # Note: throttled is enabled for binary lens because computation time is significantly longer
        self.set_mod_slider_throttle()
        
        # Clear error message if no errors
        self.slider_error_msg.object = None


    def _update_param_table_change(self, *event):
        # Note: param_table_change happens from param_table edits
        self.current_param_change = self.param_table.value.index[event[0].row]
        self._update_sliders()


    def _update_param_values(self, *event):
        # Note: the '*event' argument is used to set dependency on sliders

        # Lock needed to prevent excessive triggers when changing parameter sliders through parameterization or data table change
        if self.lock_trigger == False:
            
            # Function triggered by a slider
            if event != ():
                # Regex is used to get just the parameter name and not the unit
                param_name = re.match(r'[^\W\\[]*', event[0].obj.name).group()

                self.current_param_change = param_name

                # Change data frame value and range table
                param_df = self.param_table.value
                param_df.loc[(param_name, 'Value')] = self.param_sliders[param_name].value

                self.param_table.value = param_df

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
    

    def set_mod_slider_throttle(self, *event):
        # Lock needed to prevent overlap with changing data table (the function is called after num_pts is changed)
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

