################################################
# Packages
################################################
import numpy as np
import plotly.graph_objects as go

from BAGLE_Microlensing.src.bagle import model
import celerite

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import traces, constants
from app_components import indicators, paramztn_select, settings_tabs


################################################
# Dashboard - Plots
################################################
class PlotPanel(Viewer):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)

    # Lists for the set of photometry plots and set of astrometry plots selected in plot checkbox
    selected_phot_plots, selected_ast_plots = param.List(), param.List()

    # Lists for the set of photometry traces and set of astrometry traces
    main_phot_keys, extra_phot_keys = param.List(default = []), param.List(default = [])
    main_ast_keys, extra_ast_keys = param.List(default = []), param.List(default = [])
    
    # Labels for plot
    plot_names = constants.PHOT_PLOT_NAMES + constants.AST_PLOT_NAMES

    # Tuples for what keys have a time trace, a full trace, or a time marker
    time_trace_keys = ('non_gp', 'gp_prior', 'gp_predict', 'gp_samps',
                       'unres_len', 'unres_unlen', 
                       'ps_res_len',
                       'bs_res_unlen_pri', 'bs_res_len_pri', 'bs_res_unlen_sec', 'bs_res_len_sec',
                       'lens')
    full_trace_keys = ('non_gp', 'gp_prior', 'gp_predict',
                       'unres_len', 'unres_unlen', 
                       'bs_res_unlen_pri', 'bs_res_unlen_sec', 
                       'lens')
    marker_keys = ('non_gp', 'gp_prior', 'gp_predict',
                   'unres_len', 'unres_unlen', 
                   'ps_res_len',
                   'bs_res_unlen_pri', 'bs_res_len_pri', 'bs_res_unlen_sec', 'bs_res_len_sec',
                   'lens')


    ########################
    # General Methods
    ########################
    def __init__(self, **params):
        # 'time' is a numpy array of times
        # 'mod' is an instance of a BAGLE model
        # 'gp' is a celerite GP object with gp.compute performed
        self.time, self.mod, self.gp = None, None, None

        # Complex image position and amplification arrays for binary lens models (these are numpy arrays)
        self.bl_image_arr, self.bl_amp_arr = None, None

        # Defining traces
        self.phot_traces = {
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

        self.ast_traces = {
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
                pri_clr = 'rgb(148, 52, 110)', sec_clr = 'rgb(202, 104, 163)',
                time_width = 2, full_width  = 1.5, marker_size = 10
            )
        }

        # Trace Update functions for astrometry traces that are in ast_checkbox
        self.extra_ast_fns = {
            'ps_res_len': self._update_ps_res_len,
            'bs_res_unlen': self._update_bs_res_unlen,
            'bs_res_len_pri': self._update_bs_res_len,
            'bs_res_len_sec': self._update_bs_res_len,
            'lens': self._update_lens
        }

        # Set up initial figure formats, plotly panes, and plot flexboxes
        self.init_figs, self.plotly_panes, self.plot_boxes = self.make_plot_components(self.plot_names)

        # Plot row layout
        self.plot_layout = pn.FlexBox(
            objects = list(self.plot_boxes.values()),
            flex_wrap = 'nowrap',
            gap = f'{2 * (50 - constants.PLOT_WIDTH)}%',
            sizing_mode = 'stretch_both',
            styles = {'overflow':'scroll', 
                      'border':'white solid 0.01rem', 
                      'background':constants.CLRS['secondary']}
        )
    
        # Define dependencies
        super().__init__(**params)
        self.settings_info.param_sliders['Num_pts'].param.watch(self._update_mod_components, 'value_throttled')

        self.settings_info.param_sliders['Num_samps'].param.watch(self._update_gp_samps, 'value')
        self.settings_info.param_sliders['Num_samps'].param.watch(self._update_phot_plots, 'value')

        self.settings_info.param_sliders['Time'].param.watch(self._update_phot_plots, 'value')
        self.settings_info.param_sliders['Time'].param.watch(self._update_ast_plots, 'value')

    def make_plot_components(self, plot_names):
        init_figs, plotly_panes, plot_boxes = {}, {}, {}
        for name in plot_names:
            # Make initial figure formats
            fig = go.Figure()
            fig.update_xaxes(
                title = constants.FORMAT_DICT[name][1][0],
                title_font_size = constants.FONTSIZES['plot_axes_labels'],
                ticks = 'outside', tickformat = '000',
                color = 'white',
                gridcolor = constants.CLRS['gridline'], zeroline = False
            )
            fig.update_yaxes(
                title = constants.FORMAT_DICT[name][1][1],
                title_font_size = constants.FONTSIZES['plot_axes_labels'],
                ticks = 'outside', tickformat = '000',
                color = 'white',
                gridcolor = constants.CLRS['gridline'], zeroline = False
            )
            fig.update_layout(
                title = dict(text = constants.FORMAT_DICT[name][0], y = 0.98,
                             font = dict(color = 'white', 
                                         size = constants.FONTSIZES['plot_title'])),
                plot_bgcolor = constants.CLRS['secondary'], 
                paper_bgcolor = constants.CLRS['secondary'],
                font_size = constants.FONTSIZES['plot_axes_ticks'],
                legend = dict(grouptitlefont_color = 'white'),
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
                styles = constants.BASE_PLOTBOX_STYLE
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

    @pn.depends('settings_info.dashboard_checkbox.value', watch = True)
    def _update_selected_plots(self):
        self.selected_phot_plots = list(set(constants.PHOT_PLOT_NAMES) & set(self.settings_info.dashboard_checkbox.value))
        self.selected_ast_plots = list(set(constants.AST_PLOT_NAMES) & set(self.settings_info.dashboard_checkbox.value))

    @pn.depends('settings_info.trigger_param_change', watch = True)
    def _update_mod_components(self, *event):
        # Note: '*event' is needed for 'Num_pts' watcher
    
        # Note: lock needed to guard against Num_pts slider reset because trigger_param_change also triggers the update
            # See chain: set_default_table_and_checkboxes => update_sliders => _update_param_values in settings_tabs.SettingsTabs class
        if self.settings_info.lock_trigger == False:
            self.time = np.linspace(start = self.settings_info.param_sliders['Time'].start, 
                                    stop = self.settings_info.param_sliders['Time'].end, 
                                    num = self.settings_info.param_sliders['Num_pts'].value)
            
            # Check for bad parameter combination (e.g. dL > dS)  
            # try:
                # Check if 'Num_pts' slider is disabled
                    # Note: this assumes that the 'Num_pts' slider will never cause an exception, which should be true
            if self.settings_info.param_sliders['Num_pts'].disabled == True:
                self.settings_info.set_slider_errored_layout(undo = True)

            # Set model
            self.mod = getattr(model, self.paramztn_info.selected_paramztn)(**self.settings_info.mod_param_values)

            # Check if throttled Num_pts was the event
            if (event != ()) and (event[0].obj.name == self.settings_info.param_sliders['Num_pts'].name):
                self.set_loading_layout()
            
            # Check if parameter sliders are throttled
            elif self.settings_info.throttled == True:
                self.set_loading_layout()

            # Update photometry
            # Note: there are currently no extra photometry traces from phot_checkbox
                # I'm including GP samples as a main trace here, despite its dependency on 'Num_samps'
            self._update_main_phot_traces()
            self._update_phot_plots()

            # Update astrometry
            self._update_main_ast_traces()
            self._update_extra_ast_traces()
            self._update_ast_plots()

            # except:
            #     self.settings_info.set_slider_errored_layout(undo = False)

    ########################
    # Photometry Methods
    ######################## 
    @pn.depends('selected_phot_plots', watch = True)
    def _update_main_phot_traces(self):
        # Check if photometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_phot_plots) != 0) and (self.settings_info.lock_trigger == False):
            # Check for GP
            if 'GP' not in self.paramztn_info.selected_paramztn:
                phot = self.mod.get_photometry(self.time)
                self.phot_traces['non_gp'].update_traces(phot, self.time)

                # Reset phot keys
                self.main_phot_keys = ['non_gp']
            else:
                selected_params = self.paramztn_info.selected_params
                mod_param_values = self.settings_info.mod_param_values

                cel_mod = model.Celerite_GP_Model(self.mod, 0)
                    
                # Matern-3/2 parameters
                log_sig = mod_param_values['gp_log_sigma']

                if 'gp_rho' in selected_params:
                    log_rho = np.log(mod_param_values['gp_rho'])
                elif 'gp_log_rho' in selected_params:
                    log_rho = mod_param_values['gp_log_rho']

                # DDSHO parameters
                gp_log_Q = np.log(2**-0.5)
                log_omega0 = mod_param_values['gp_log_omega0']

                if 'gp_log_S0'in selected_params:
                    log_S0 = mod_param_values['gp_log_S0']
                elif 'gp_log_omega04_S0' in selected_params:
                    log_S0 = mod_param_values['gp_log_omega04_S0'] - (4 * log_omega0)    
                elif 'gp_log_omega0_S0' in selected_params:
                    log_S0 = mod_param_values['gp_log_omega0_S0'] - log_omega0
    
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
                # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
            selected_time_keys = [key for key in self.time_trace_keys if key in selected_trace_keys]
            all_phot = []
            
            for key in selected_time_keys:
                self.phot_traces[key].plot_time(fig = phot_fig, time_idx = time_idx)
                all_phot += self.phot_traces[key].get_phot_list()

            # Get all keys with a full trace and plot them
                # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
            if 'full_trace' in self.settings_info.genrl_plot_checkbox.value:
                selected_full_keys = [key for key in self.full_trace_keys if key in selected_trace_keys]

                for key in selected_full_keys:
                    self.phot_traces[key].plot_full(fig = phot_fig)

            # Get all keys with a marker trace and plot them
                # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
            if 'marker' in self.settings_info.genrl_plot_checkbox.value:
                selected_marker_keys = [key for key in self.marker_keys if key in selected_trace_keys]

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
            self.plotly_panes['phot'].object = phot_fig

            # Check if loading or error indicator is on
            if 'indicator' in self.plot_boxes['phot'].objects[0].name:
                self.plot_boxes['phot'].objects = [self.plotly_panes['phot']]

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

            for plot_name in self.selected_ast_plots:

                # Create figure
                ast_fig = go.Figure(self.init_figs[plot_name])

                # Get all trace keys that are to be plotted
                selected_trace_keys = set(self.extra_ast_keys + self.main_ast_keys)

                # Get all keys with a time trace and plot them
                    # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
                selected_time_keys = [key for key in self.time_trace_keys if key in selected_trace_keys]
                all_x, all_y = [], []

                for trace_key in selected_time_keys:
                    self.ast_traces[trace_key].plot_time(fig = ast_fig, plot_name = plot_name, time_idx = time_idx)
                    x_list, y_list = self.ast_traces[trace_key].get_xy_lists(plot_name = plot_name)
                    all_x += x_list
                    all_y += y_list

                # Get all keys with a full trace and plot them
                    # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
                if 'full_trace' in self.settings_info.genrl_plot_checkbox.value:
                    selected_full_keys = [key for key in self.full_trace_keys if key in selected_trace_keys]

                    for trace_key in selected_full_keys:
                        self.ast_traces[trace_key].plot_full(fig = ast_fig, plot_name = plot_name)

                # Get all keys with a marker trace and plot them
                    # Note: putting selected_trace_keys first takes longer, but makes ordering much easier
                if 'marker' in self.settings_info.genrl_plot_checkbox.value:
                    selected_marker_keys = [key for key in self.marker_keys if key in selected_trace_keys]

                    for trace_key in selected_marker_keys:
                        self.ast_traces[trace_key].plot_marker(fig = ast_fig, plot_name = plot_name, marker_idx = time_idx[-1])

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
    