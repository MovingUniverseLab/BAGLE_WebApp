################################################
# Packages
################################################
import numpy as np
import plotly.graph_objects as go
import threading
import traceback

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import indicators, traces, styles
from app_components import paramztn_select, settings_tabs, color_panel


################################################
# Dashboard - Plot Panel
################################################
class PlotPanel(Viewer):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)
    trace_info = param.ClassSelector(class_ = traces.AllTraceInfo)
    clr_info = param.ClassSelector(class_ = color_panel.ColorPanel)

    ########################
    # General Methods
    ########################
    def __init__(self, **params):
        super().__init__(**params)

        self.time_fn_dependency = {
            'throttled': False, # Parameter to determine if time slider is throttled
            'watchers': [], # List of watchers for time slider
            'functions': [self._update_plot_time] # List of functions with time slider dependency
        }

        # Set up initial figure formats with default theme
        self.base_figs = {}
        self._update_base_figs()

        # Make plotly panes, and plot flexboxes
        self.plotly_panes, self.plot_boxes = self.make_plot_components()

        # Plot row layout
        self.plot_layout = pn.FlexBox(
            objects = list(self.plot_boxes.values()),
            flex_wrap = 'nowrap',
            gap = f'{2 * (50 - styles.PLOT_WIDTH)}%',
            sizing_mode = 'stretch_both',
            styles = {'overflow-x':'scroll',
                      'border':f'{styles.CLRS["page_border"]} solid 0.01rem',
                      'border-top':'transparent',
                      'border-bottom':'transparent'}
        )
    
        # Define dependencies
        self.set_time_slider_throttle()
        self.settings_info.param_sliders['Num_pts'].param.watch(self._update_all_plots, 'value_throttled')
        self.settings_info.param_sliders['Num_pts'].param.watch(self.set_time_slider_throttle, 'value')

        # Note: precedence here makes sure that 'self._update_phot_plots' happens after 'self.trace_info._update_gp_samps'
        self.settings_info.param_sliders['Num_samps'].param.watch(self._update_phot_plots, 'value', precedence = 10)

        for clr_picker in self.clr_info.fig_clr_pickers.values():
            clr_picker.param.watch(self._update_base_figs, 'value')

        for trace_key in self.clr_info.trace_clr_pickers.keys():
            if 'clr_cycle' not in self.clr_info.trace_clr_pickers[trace_key].keys():
                all_clr_pickers = self.clr_info.trace_clr_pickers[trace_key].values()
            else:
                all_clr_pickers = self.clr_info.trace_clr_pickers[trace_key]['clr_cycle']
            
            for clr_picker in all_clr_pickers:
                clr_picker.param.watch(self._update_trace_clrs, 'value')
        
        self.clr_info.theme_dropdown.param.watch(self.set_plot_theme, 'value')

        for error_bool in self.settings_info.errored_state.values():
            error_bool.param.watch(self.set_errored_layout, 'value')


    def make_plot_components(self):
        plotly_panes, plot_boxes = {}, {}
        for name in styles.ALL_PLOT_NAMES:
            # Make plotly pane
            plotly_configs = {
                'toImageButtonOptions': {'filename': name, 'scale': 3}, 
                'displayModeBar': True, 'displaylogo': False,
                'modeBarButtonsToRemove': ['autoScale', 'lasso', 'select']
            }
            pane = pn.pane.Plotly(
                name = name,
                config = plotly_configs,
                sizing_mode = 'stretch_both',
                margin = 0
            )
            plotly_panes[name] = pane

            # Make flexbox for plotly pane
            plot_boxes[name] = pn.FlexBox(
                indicators.get_indicator('obj_loading'),
                justify_content = 'center',
                align_content = 'center',
                styles = styles.BASE_PLOTBOX_STYLES
            )

        return plotly_panes, plot_boxes
        

    def set_time_slider_throttle(self, *event):
        if self.settings_info.param_sliders['Num_pts'].value >= 10000:
            self.time_fn_dependency['throttled'] = True
            dependency = 'value_throttled'
        else:
            self.time_fn_dependency['throttled'] = False
            dependency = 'value'

        # Unwatch before updating to prevent multiple repeated watchers (memory leaks)
        if len(self.time_fn_dependency['watchers']) != 0:
            for watcher in self.time_fn_dependency['watchers']:
                self.settings_info.param_sliders['Time'].param.unwatch(watcher)

            self.time_fn_dependency['watchers'] = []

        # Add watcher for functions
        for function in self.time_fn_dependency['functions']:
            watcher = self.settings_info.param_sliders['Time'].param.watch(function, dependency)
            self.time_fn_dependency['watchers'].append(watcher)


    def set_errored_layout(self, *event):
        if event[0].obj.value == True:
            for name in styles.ALL_PLOT_NAMES:
                self.plot_boxes[name].objects = [indicators.get_indicator('error')]


    def set_loading_layout(self):
        for name in styles.ALL_PLOT_NAMES:
            self.plot_boxes[name].objects = [indicators.get_indicator('obj_loading')]


    ########################
    # Coloring Methods
    ######################## 
    @pn.depends('settings_info.genrl_plot_checkbox.value', watch = True)
    def _update_base_figs(self, *event):
        # Note: '*event' is used for the dependencies of the color pickers in 'clr_info.fig_clr_pickers'

        if self.clr_info.lock_trigger == False:

            # Create color dictionary
            clr_dict = {key:self.clr_info.fig_clr_pickers[key].value for key in self.clr_info.fig_clr_pickers.keys()}

            # Create new base figures
            for name in styles.ALL_PLOT_NAMES:

                # Make initial figure formats
                fig = go.Figure()
                fig.update_xaxes(
                    title = styles.ALL_FORMATS[name][1][0],
                    title_font_size = styles.FONTSIZES['plot_axes_labels'],
                    ticks = 'outside', tickformat = '000', 
                    tickcolor = clr_dict['ticks'], 
                    tickfont_color = clr_dict['ticks'], 
                    color = clr_dict['labels'], 
                    gridcolor = clr_dict['gridlines'], zeroline = False
                )
                fig.update_yaxes(
                    title = styles.ALL_FORMATS[name][1][1],
                    title_font_size = styles.FONTSIZES['plot_axes_labels'],
                    ticks = 'outside', tickformat = '000',
                    tickcolor = clr_dict['ticks'], 
                    tickfont_color = clr_dict['ticks'], 
                    color = clr_dict['labels'], 
                    gridcolor = clr_dict['gridlines'], zeroline = False
                )
                fig.update_layout(
                    plot_bgcolor = clr_dict['plot_bg'], 
                    paper_bgcolor = clr_dict['paper_bg'], 
                    font_size = styles.FONTSIZES['plot_axes_ticks'],
                    legend = dict(grouptitlefont_color = clr_dict['labels'], itemsizing = 'constant'),
                    margin = dict(l = 75, r = 5, t = 30, b = 55),
                    title = dict(y = 0.98, font = dict(color = clr_dict['labels'], size = styles.FONTSIZES['plot_title']))
                )
                self.base_figs[name] = fig

                # Check if title/gridlines should be shown
                if 'title' in self.settings_info.genrl_plot_checkbox.value:
                    fig.update_layout(title_text = styles.ALL_FORMATS[name][0])

                if 'gridlines' not in self.settings_info.genrl_plot_checkbox.value:
                    fig.update_xaxes(showgrid = False)
                    fig.update_yaxes(showgrid = False)
                    
            # Reverse y-axis for photometry magnitude
            for name in styles.PHOT_PLOT_NAMES:
                self.base_figs[name].update_yaxes(autorange = 'reversed')

            # Change layout of currently displayed figures to new base figures
                # Note: 'settings_info.lock_trigger' is used here to guard against 'settings_info.genrl_plot_checkbox' reset, which will lead to a change before any figures are displayed
            if self.settings_info.lock_trigger == False:
                for plot_name in (self.trace_info.selected_phot_plots + self.trace_info.selected_ast_plots):
                    self.plotly_panes[plot_name].object['layout'] = self.base_figs[plot_name]['layout']


    def _update_trace_clrs(self, *event):
        '''
        This function is always triggered by a single color picker
        '''
        if self.clr_info.lock_trigger == False:
            # This should be a tuple of the form (trace key, color type, ...), where ... is the color cycle index if color type is color cycle
                # See the 'make_trace_clrs_layout' in app_components.color_panel
            clr_picker_id = eval(event[0].obj.description)

            trace_key, clr_type = clr_picker_id[0], clr_picker_id[1]
            trace_uid_list = [] # This is a list to store all unique ids of traces whose colors are to be changed

            # Check if the trace is in a photometry or an astrometry plot
            if trace_key in self.trace_info.main_phot_keys + self.trace_info.extra_phot_keys:
                trace_plot_names = self.trace_info.selected_phot_plots
            else:
                trace_plot_names = self.trace_info.selected_ast_plots
            
            # Check if color type is pri_clr, sec_clr, or clr_cycle
                # clr_cycle is a special case currently used for only GP samples
            if clr_type != 'clr_cycle':
                trace_uid_list.append(f'{trace_key}-{clr_type}')

                # Change the attribute of the trace to keep the color change when updating plot
                setattr(self.trace_info.all_traces[trace_key], clr_type, event[0].obj.value)

            else:
                # Check if color pickers for the color cycle are linked
                if self.clr_info.clr_cycle_tools[trace_key, 'link_switch'].value == True:
                    # Lock trigger to prevent looping
                    self.clr_info.lock_trigger = True
                    
                    # Change value of each color picker
                    for cycle_idx, clr_picker in enumerate(self.clr_info.trace_clr_pickers[trace_key]['clr_cycle']):
                        clr_picker.value = event[0].obj.value
                        trace_uid_list.append(f'{trace_key}-clr_cycle-{cycle_idx}')

                    self.clr_info.lock_trigger = False

                    # Change the attribute of the trace to keep the color change when updating plot
                    self.trace_info.all_traces[trace_key].clr_cycle = [event[0].obj.value] * len(self.trace_info.all_traces[trace_key].clr_cycle)

                else:
                    # Index for which part of the color cycle was changed
                    cycle_idx = clr_picker_id[2]    
                    trace_uid_list.append(f'{trace_key}-clr_cycle-{cycle_idx}')

                    # Change the attribute of the trace to keep the color change when updating plot
                    self.trace_info.all_traces[trace_key].clr_cycle[cycle_idx] = event[0].obj.value

            # Change color of relevant traces that are currently displayed
            for plot_name in trace_plot_names:
                fig = self.plotly_panes[plot_name].object
                for trace_uid in trace_uid_list:
                    fig.update_traces(line_color = event[0].obj.value, marker_color = event[0].obj.value, selector = dict(uid = trace_uid))

                
    # @pn.depends('clr_info.theme_dropdown.value', watch = True)
    def set_plot_theme(self, *event):
        theme_dict = self.clr_info.theme_dropdown.value
        if theme_dict != 'None':
            # Change theme of traces
            self.trace_info.set_trace_theme(theme_dict)

            # Change theme of the figure
                # Note: the figure color pickers should have already been changed through styles
                # Also, the lock here is used to prevent repeated patches. Although, this isn't too much of a problem since Panel knows to drop repeated patches.
            self.settings_info.lock_trigger = True
            self._update_base_figs()
            self.settings_info.lock_trigger = False

            # Replot everything
            self.set_loading_layout()
            self._update_phot_plots()
            self._update_ast_plots()


    ########################
    # Plotting Methods
    ######################## 
    @pn.depends('settings_info.trigger_param_change', watch = True)
    def _update_all_plots(self, *event):
        # Note: '*event' is needed for 'Num_pts' watcher
    
        # Note: lock needed to guard against Num_pts slider reset because trigger_param_change also triggers the update
            # See chain: set_default_tabs => _update_sliders => _update_param_values in settings_tabs.SettingsTabs class
        if self.settings_info.lock_trigger == False:

            # Check for bad parameter combination (e.g. dL > dS)  
            try:
                self.settings_info.set_param_errored_layout(undo = True)

                # Check if throttled Num_pts was the event
                if (event != ()) and (event[0].obj.name == self.settings_info.param_sliders['Num_pts'].name):
                    self.set_loading_layout()

                # Check if parameter sliders are throttled
                elif self.settings_info.throttled == True:
                    self.set_loading_layout()
                
                # Update traces
                # Note: It's possible to set the 'trigger_param_change' and 'Num_pts' dependency directly in trace.py for this function.
                    # However, I chose to put it here to make error catching easier.
                self.trace_info.update_all_traces()

                # Update plots
                self._update_phot_plots()
                self._update_ast_plots()
    
            except:
                print('AN ERROR HAS OCCURRED:\n', traceback.format_exc())
                self.settings_info.set_param_errored_layout(undo = False)


    def _update_plot_time(self, *event):
        # Check if time slider is throttled
        if self.time_fn_dependency['throttled'] == True:
            self.set_loading_layout()

        # Update plots
        self._update_phot_plots()
        self._update_ast_plots()       


    @pn.depends('settings_info.dashboard_checkbox.value', 'settings_info.phot_checkbox.value', 'settings_info.genrl_plot_checkbox.value', watch = True)
    def _update_phot_plots(self, *event):
        # Note: '*event' is needed for 'Time' and 'Num_samps' watcher

        # Check if photometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.trace_info.selected_phot_plots) != 0) and (self.settings_info.lock_trigger == False):
            time = self.trace_info.cache['time']

            # Get times that are less than or equal to Time slider
            time_idx = np.where(time <= self.settings_info.param_sliders['Time'].value)[0]

            # This part may need to be changed if we add more types of photometry plots
                # e.g. we could loop through names in styles.PHOT_PLOT_NAMES

            # Create photometry figure
            phot_fig = go.Figure(self.base_figs['phot'])

            selected_trace_keys = set(self.trace_info.main_phot_keys + self.trace_info.extra_phot_keys)

            # Get all keys with a time trace and plot them
            selected_time_keys = [key for key in self.trace_info.trace_types['plot_time'] if key in selected_trace_keys]
            all_phot = []
            
            for trace_key in selected_time_keys:
                trace = self.trace_info.all_traces[trace_key]
                trace.plot_time(fig = phot_fig, time_idx = time_idx)
                all_phot += trace.get_phot_list()

            # Get all keys with a full trace and plot them
            if 'full_trace' in self.settings_info.genrl_plot_checkbox.value:
                selected_full_keys = [key for key in self.trace_info.trace_types['plot_full'] if key in selected_trace_keys]

                for trace_key in selected_full_keys:
                    self.trace_info.all_traces[trace_key].plot_full(fig = phot_fig)

            # Get all keys with a marker trace and plot them
            if 'marker' in self.settings_info.genrl_plot_checkbox.value:
                selected_marker_keys = [key for key in self.trace_info.trace_types['plot_marker'] if key in selected_trace_keys]

                for trace_key in selected_marker_keys:
                    self.trace_info.all_traces[trace_key].plot_marker(fig = phot_fig, marker_idx = time_idx[-1])

            # Set up traces to fix axis limits
            min_time, max_time = np.nanmin(time), np.nanmax(time)
            min_phot, max_phot = np.nanmin(all_phot), np.nanmax(all_phot)

            traces.add_limit_trace(
                fig = phot_fig, 
                x_limits = [min_time, max_time],
                y_limits = [min_phot, max_phot]
            )

            # Update photometry pane with figure
            self.plotly_panes['phot'].object = phot_fig

            # Check if loading or error indicator is on
            if self.plot_boxes['phot'].objects[0].name != self.plotly_panes['phot'].name:
                self.plot_boxes['phot'].objects = [self.plotly_panes['phot']]


    @pn.depends('settings_info.dashboard_checkbox.value', 'settings_info.ast_checkbox.value', 'settings_info.genrl_plot_checkbox.value', watch = True)
    def _update_ast_plots(self, *event):
        # Note: '*event' is needed for 'Time' watcher

        # Check if astrometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.trace_info.selected_ast_plots) != 0) and (self.settings_info.lock_trigger == False):
            time = self.trace_info.cache['time']

            # Get times that are less than or equal to Time slider
            time_idx = np.where(time <= self.settings_info.param_sliders['Time'].value)[0]

            # Get all trace keys that are to be plotted
            selected_keys = {}
            selected_keys['all'] = set(self.trace_info.extra_ast_keys + self.trace_info.main_ast_keys)

            # Get all selected keys with a time trace
                # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
            selected_keys['time'] = [key for key in self.trace_info.trace_types['plot_time'] if key in selected_keys['all']]

            # Get all selected keys with a full trace
                # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
            if 'full_trace' in self.settings_info.genrl_plot_checkbox.value:
                selected_keys['full'] = [key for key in self.trace_info.trace_types['plot_full'] if key in selected_keys['all']]

            # Get all selected keys with a marker
                # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
            if 'marker' in self.settings_info.genrl_plot_checkbox.value:
                selected_keys['marker'] = [key for key in self.trace_info.trace_types['plot_marker'] if key in selected_keys['all']]

            for plot_name in self.trace_info.selected_ast_plots:
                plotting_thread = threading.Thread(target = self._update_single_ast, args = (plot_name, time_idx, selected_keys))
                plotting_thread.start()

    def _update_single_ast(self, plot_name, time_idx, selected_keys):
        # Create figure
        ast_fig = go.Figure(self.base_figs[plot_name])

        all_x, all_y = [], []

        # Plot time traces
        for trace_key in selected_keys['time']:
            trace = self.trace_info.all_traces[trace_key]
            trace.plot_time(fig = ast_fig, plot_name = plot_name, time_idx = time_idx)
            x_list, y_list = trace.get_xy_lists(plot_name = plot_name)
            all_x += x_list
            all_y += y_list

        # Plot full traces
        if 'full_trace' in self.settings_info.genrl_plot_checkbox.value:
            for trace_key in selected_keys['full']:
                self.trace_info.all_traces[trace_key].plot_full(fig = ast_fig, plot_name = plot_name)

        # Plot markers
        if 'marker' in self.settings_info.genrl_plot_checkbox.value:
            for trace_key in selected_keys['marker']:
                self.trace_info.all_traces[trace_key].plot_marker(fig = ast_fig, plot_name = plot_name, marker_idx = time_idx[-1])

        # Set up traces to fix axis limits
        min_x, max_x = np.nanmin(all_x), np.nanmax(all_x)
        min_y, max_y = np.nanmin(all_y), np.nanmax(all_y)

        traces.add_limit_trace(
            fig = ast_fig, 
            x_limits = [min_x, max_x],
            y_limits = [min_y, max_y]
        )

        # Update astrometry pane with figure
        self.plotly_panes[plot_name].object = ast_fig

        # Check if loading or error indicator is on
        if self.plot_boxes[plot_name].objects[0].name != self.plotly_panes[plot_name].name:
                self.plot_boxes[plot_name].objects = [self.plotly_panes[plot_name]]


    ########################
    # Panel Component
    ######################## 
    def __panel__(self):
        return self.plot_layout
    