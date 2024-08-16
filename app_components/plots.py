################################################
# Packages
################################################
import numpy as np
import plotly.graph_objects as go

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import indicators, traces, styles
from app_components import paramztn_select, settings_tabs


################################################
# Dashboard - Plot Panel
################################################
class PlotPanel(Viewer):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)
    trace_info = param.ClassSelector(class_ = traces.AllTraceInfo)
    
    # Labels for plot
    plot_names = styles.PHOT_PLOT_NAMES + styles.AST_PLOT_NAMES


    ########################
    # General Methods
    ########################
    def __init__(self, **params):
        # Set up initial figure formats, plotly panes, and plot flexboxes
        self.init_figs, self.plotly_panes, self.plot_boxes = self.make_plot_components(self.plot_names)

        # Plot row layout
        self.plot_layout = pn.FlexBox(
            objects = list(self.plot_boxes.values()),
            flex_wrap = 'nowrap',
            gap = f'{2 * (50 - styles.PLOT_WIDTH)}%',
            sizing_mode = 'stretch_both',
            styles = {'overflow':'scroll',
                      'border':f'{styles.CLRS["page_border"]} solid 0.01rem',
                      'border-top':'transparent',
                      'border-bottom':'transparent'}
        )
    
        # Define dependencies
        super().__init__(**params)
        self.settings_info.param_sliders['Num_pts'].param.watch(self._update_all_plots, 'value_throttled')

        # Note: precedence here makes sure that 'self._update_phot_plots' happens after 'self.trace_info._update_gp_samps'
        self.settings_info.param_sliders['Num_samps'].param.watch(self._update_phot_plots, 'value', precedence = 10)

        self.settings_info.param_sliders['Time'].param.watch(self._update_phot_plots, 'value')
        self.settings_info.param_sliders['Time'].param.watch(self._update_ast_plots, 'value')


    def make_plot_components(self, plot_names):
        init_figs, plotly_panes, plot_boxes = {}, {}, {}
        for name in plot_names:
            # Make initial figure formats
            fig = go.Figure()
            fig.update_xaxes(
                title = styles.FORMAT_DICT[name][1][0],
                title_font_size = styles.FONTSIZES['plot_axes_labels'],
                ticks = 'outside', tickformat = '000',
                color = styles.CLRS['txt_primary'],
                gridcolor = styles.CLRS['plot_gridline'], zeroline = False
            )
            fig.update_yaxes(
                title = styles.FORMAT_DICT[name][1][1],
                title_font_size = styles.FONTSIZES['plot_axes_labels'],
                ticks = 'outside', tickformat = '000',
                color = styles.CLRS['txt_primary'],
                gridcolor = styles.CLRS['plot_gridline'], zeroline = False
            )
            fig.update_layout(
                plot_bgcolor = styles.CLRS['page_secondary'], 
                paper_bgcolor = styles.CLRS['page_secondary'],
                font_size = styles.FONTSIZES['plot_axes_ticks'],
                legend = dict(grouptitlefont_color = styles.CLRS['txt_primary'], itemsizing = 'constant'),
                margin = dict(l = 75, r = 5, t = 30, b = 55)
            )
            init_figs[name] = fig

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
                indicators.loading,
                justify_content = 'center',
                align_content = 'center',
                styles = styles.BASE_PLOTBOX_STYLES
            )

         # Reverse y-axis for photometry magnitude
        init_figs['phot'].update_yaxes(autorange = 'reversed')

        return init_figs, plotly_panes, plot_boxes


    @pn.depends('settings_info.error_trigger', watch = True)
    def set_errored_layout(self):
        for name in self.plot_names:
            self.plot_boxes[name].objects = [indicators.error]


    def set_loading_layout(self):
        for name in self.plot_names:
            self.plot_boxes[name].objects = [indicators.loading]


    @pn.depends('settings_info.trigger_param_change', watch = True)
    def _update_all_plots(self, *event):
        # Note: '*event' is needed for 'Num_pts' watcher
    
        # Note: lock needed to guard against Num_pts slider reset because trigger_param_change also triggers the update
            # See chain: set_default_tabs => _update_sliders => _update_param_values in settings_tabs.SettingsTabs class
        if self.settings_info.lock_trigger == False:
            print('UPDATING ALL PLOTS:::::')

            # # Check for bad parameter combination (e.g. dL > dS)  
            # try:
            # Check if 'Num_pts' slider is disabled, if so, this implies that most other sliders are also disabled
                # Note: this assumes that the 'Num_pts' slider will never cause an exception, which should be true
            if self.settings_info.param_sliders['Num_pts'].disabled == True:
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

            # except:
            #     self.settings_info.set_param_errored_layout(undo = False)


    ########################
    # Photometry Methods
    ######################## 
    @pn.depends('settings_info.dashboard_checkbox.value', 'settings_info.phot_checkbox.value', 'settings_info.genrl_plot_checkbox.value', watch = True)
    def _update_phot_plots(self, *event):
        # Note: '*event' is needed for 'Time' and 'Num_samps' watcher

        # Check if photometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.trace_info.selected_phot_plots) != 0) and (self.settings_info.lock_trigger == False):
            print('UPDATING PHOTOMETRY PLOT')
            time = self.trace_info.cache['time']

            # Get times that are less than or equal to Time slider
            time_idx = np.where(time <= self.settings_info.param_sliders['Time'].value)[0]

            # Create photometry figure
            phot_fig = go.Figure(self.init_figs['phot'])

            # Check if title should be shown
            if 'title' in self.settings_info.genrl_plot_checkbox.value:
                phot_fig.update_layout(
                    title = dict(text = styles.FORMAT_DICT['phot'][0], y = 0.98,
                    font = dict(color = styles.CLRS['txt_primary'], size = styles.FONTSIZES['plot_title'])),
                )

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
            if 'indicator' in self.plot_boxes['phot'].objects[0].name:
                self.plot_boxes['phot'].objects = [self.plotly_panes['phot']]


    ########################
    # Astrometry Methods
    ######################## 
    @pn.depends('settings_info.dashboard_checkbox.value', 'settings_info.ast_checkbox.value', 'settings_info.genrl_plot_checkbox.value', watch = True)
    def _update_ast_plots(self, *event):
        # Note: '*event' is needed for 'Time' watcher

        # Check if astrometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.trace_info.selected_ast_plots) != 0) and (self.settings_info.lock_trigger == False):
            print('UPDATING ASTROMETRY PLOT')
            time = self.trace_info.cache['time']

            # Get times that are less than or equal to Time slider
            time_idx = np.where(time <= self.settings_info.param_sliders['Time'].value)[0]

            for plot_name in self.trace_info.selected_ast_plots:
                # Create figure
                ast_fig = go.Figure(self.init_figs[plot_name])

                # Check if title should be shown
                if 'title' in self.settings_info.genrl_plot_checkbox.value:
                    ast_fig.update_layout(
                        title = dict(text = styles.FORMAT_DICT[plot_name][0], y = 0.98,
                        font = dict(color = styles.CLRS['txt_primary'], size = styles.FONTSIZES['plot_title'])),
                    )

                # Get all trace keys that are to be plotted
                selected_trace_keys = set(self.trace_info.extra_ast_keys + self.trace_info.main_ast_keys)

                # Get all keys with a time trace and plot them
                    # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
                selected_time_keys = [key for key in self.trace_info.trace_types['plot_time'] if key in selected_trace_keys]
                all_x, all_y = [], []

                for trace_key in selected_time_keys:
                    trace = self.trace_info.all_traces[trace_key]
                    trace.plot_time(fig = ast_fig, plot_name = plot_name, time_idx = time_idx)
                    x_list, y_list = trace.get_xy_lists(plot_name = plot_name)
                    all_x += x_list
                    all_y += y_list

                # Get all keys with a full trace and plot them
                    # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
                if 'full_trace' in self.settings_info.genrl_plot_checkbox.value:
                    selected_full_keys = [key for key in self.trace_info.trace_types['plot_full'] if key in selected_trace_keys]

                    for trace_key in selected_full_keys:
                        self.trace_info.all_traces[trace_key].plot_full(fig = ast_fig, plot_name = plot_name)

                # Get all keys with a marker trace and plot them
                    # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
                if 'marker' in self.settings_info.genrl_plot_checkbox.value:
                    selected_marker_keys = [key for key in self.trace_info.trace_types['plot_marker'] if key in selected_trace_keys]

                    for trace_key in selected_marker_keys:
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
                if 'indicator' in self.plot_boxes[plot_name].objects[0].name:
                        self.plot_boxes[plot_name].objects = [self.plotly_panes[plot_name]]


    def __panel__(self):
        return self.plot_layout
    