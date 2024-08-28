################################################
# Packages
################################################
import numpy as np
import itertools
import plotly.graph_objects as go
import panel as pn
import param
import threading

from bagle import model
import celerite

from app_utils import styles
from app_components import paramztn_select, settings_tabs


################################################
# Limit Trace (For all Plots)
################################################
def add_limit_trace(fig, x_limits, y_limits):
    '''
    x_limits: a list of the form [minimum x, maximum x]
    y_limits: a list of the form [minimum y, maximum y]
    '''
    fig.add_trace(
        go.Scatter(
            x = x_limits, 
            y = y_limits,
            marker = dict(color = 'rgba(0, 0, 0, 0)', size = 10),
            mode = 'markers', 
            hoverinfo = 'skip', 
            showlegend = False
        )
    )


################################################
# All Traces
################################################
# This is a class to get an instance of all trace classes and update them
class AllTraceInfo(param.Parameterized):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)

    # Lists for the set of photometry plots and set of astrometry plots selected in plot checkbox
    selected_phot_plots, selected_ast_plots = param.List(), param.List()

    # Lists for the set of photometry traces and set of astrometry traces
    main_phot_keys, extra_phot_keys = param.List(default = []), param.List(default = [])
    main_ast_keys, extra_ast_keys = param.List(default = []), param.List(default = [])


    def __init__(self, **params):
        super().__init__(**params)
        
        # A dictionary to store objects (e.g. model, time, gp) and data that may be shared across multiple traces.
        # The purpose of this dictionary is to make it so that we don't have to repetatively call the same functions.
        self.cache = {}

        # Defining traces
        self.phot_traces = {
            'non_gp': Genrl_Phot(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                gp_trace = False,
                group_name = 'Photometry',
                zorder = 100, 
                show_legend = False,
                time_width = 2, 
                full_width  = 1.5, 
                marker_size = 10
            ),
            
            'gp_prior': Genrl_Phot(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                gp_trace = False,
                group_name = 'GP Prior Mean',
                zorder = 90, 
                show_legend = True,
                time_width = 1.5, 
                full_width  = 1, 
                marker_size = 10
            ),
            
            'gp_predict': Genrl_Phot(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                gp_trace = True,
                group_name = 'GP Predictive Mean', 
                zorder = 100, 
                show_legend = True,
                time_width = 1.5, 
                full_width  = 1, 
                marker_size = 10, 
                full_dash_style = 'solid'
            ),
            
            'gp_samps': Phot_GP_Samps(
                settings_info = self.settings_info,
                cache = self.cache,
                group_name = 'GP Prior Samples',
                time_width = 0.3,
                opacity = 0.8,
            )
        }

        self.ast_traces = {
            'unres_len': Ast_Unres(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                lensed_trace = True,
                group_name = 'Unresolved, Lensed Source(s)',
                zorder = 90,
                time_width = 1.5, 
                full_width  = 1, 
                marker_size = 8
            ),
            'unres_unlen': Ast_Unres(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                lensed_trace = False,
                group_name = 'Unresolved, Unlensed Source(s)',
                zorder = 80,
                time_width = 1.5, 
                full_width  = 1, 
                marker_size = 8
            ),
            
            'ps_res_len': Ast_PS_ResLensed(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                group_name = 'Resolved, Lensed Source Images',
                time_width = 1.2, 
                marker_size = 6
            ),
            
            'bs_res_unlen_pri': Ast_BS_ResUnlensed(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                lensed_trace = False,
                src_idx = 0, 
                group_name = 'Resolved, Unlensed Primary Source',
                zorder = 70,
                time_width = 2, 
                full_width  = 1.5, 
                marker_size = 8
            ),
            'bs_res_unlen_sec': Ast_BS_ResUnlensed(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                lensed_trace = False,
                src_idx = 1, 
                group_name = 'Resolved, Unlensed Secondary Source',
                zorder = 70,
                time_width = 2, 
                full_width  = 1.5, 
                marker_size = 8
            ),
            
            'bs_res_len_pri': Ast_BS_ResLensed(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                src_idx = 0, 
                group_name = 'Resolved, Lensed Primary Source',
                time_width = 1.2, 
                marker_size = 6
            ),
            'bs_res_len_sec': Ast_BS_ResLensed(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                src_idx = 1, 
                group_name = 'Resolved, Lensed Secondary Source',
                time_width = 1.2, 
                marker_size = 6
            ),
            
            'lens': Ast_Lens(
                paramztn_info = self.paramztn_info,
                cache = self.cache,
                group_name = 'Lens(es)',
                zorder = 100,
                time_width = 2, 
                full_width  = 1.5, 
                marker_size = 10
            )
        }

        self.all_traces = {**self.phot_traces, **self.ast_traces}
        self.trace_types = self.get_trace_types()

        # Set theme of all traces to default
        self.set_trace_theme(theme_dict = styles.DEFAULT_PLOT_THEME)

        #  # A dictionary that maps the options in self.settings_info.phot_checkbox to extra phot traces
        #     # I denote anything that is linked to self.settings_info.phot_checkbox as an extra phot trace
        # self.extra_phot_cb_map = {}

        # A dictionary that maps the options in self.settings_info.ast_checkbox to extra ast traces
            # I denote anything that is linked to self.settings_info.ast_checkbox as an extra ast trace
            # We might need a function for this if mapping gets more complicated and parameterization-dependent
        self.extra_ast_cb_map = {
                'ps_res_len': ['ps_res_len'],
                'bs_res_unlen': ['bs_res_unlen_pri', 'bs_res_unlen_sec'],
                'bs_res_len_pri': ['bs_res_len_pri'],
                'bs_res_len_sec': ['bs_res_len_sec'],
                'lens': ['lens']
        }

        # Set dependencies
        self.param.watch(self._update_main_phot_traces, 'selected_phot_plots')
        self.param.watch(self._update_main_ast_traces, 'selected_ast_plots', precedence = 0)
        self.param.watch(self._update_extra_ast_traces, 'selected_ast_plots', precedence = 1)
        self.settings_info.param_sliders['Num_samps'].param.watch(self._update_gp_samps, 'value', precedence = 0)


    def get_trace_types(self):
        # Dictionary to indicate which traces have a time, full, and marker trace
        trace_types = {
            'plot_time': [],
            'plot_full': [],
            'plot_marker': []
        }

        for trace_key in self.all_traces.keys():
            # Get trace dependencies
            trace_fns = dir(self.all_traces[trace_key])

            for type_name in trace_types.keys():
                if type_name in trace_fns:
                    trace_types[type_name].append(trace_key)

        return trace_types


    def set_trace_theme(self, theme_dict):
        for trace_key in self.all_traces.keys():
            trace = self.all_traces[trace_key]
            for clr_key in theme_dict[trace_key].keys():
                setattr(trace, clr_key, theme_dict[trace_key][clr_key])


    @pn.depends('settings_info.dashboard_checkbox.value', watch = True)
    def _update_selected_plots(self):
        self.selected_phot_plots = [name for name in styles.PHOT_PLOT_NAMES if name in self.settings_info.dashboard_checkbox.value]
        self.selected_ast_plots = [name for name in styles.AST_PLOT_NAMES if name in self.settings_info.dashboard_checkbox.value]


    def update_all_traces(self):
        time = np.linspace(start = self.settings_info.param_sliders['Time'].start, 
                           stop = self.settings_info.param_sliders['Time'].end, 
                           num = self.settings_info.param_sliders['Num_pts'].value)
        
        # Check if 'Time slider' value is in time
        time_value = self.settings_info.param_sliders['Time'].value
        if time_value not in time:
            time = np.sort(np.append(time, time_value))
        
        # Update the model and time array in cache
        self.cache['mod'] = getattr(model, self.paramztn_info.selected_paramztn)(**self.settings_info.mod_param_values)
        self.cache['time'] = time

        # Update photometry
        # Note: there are currently no extra photometry traces from phot_checkbox
            # I'm including GP samples as a main trace here, despite its dependency on 'Num_samps'
        self._update_main_phot_traces()

        # Update astrometry
        self._update_main_ast_traces()
        self._update_extra_ast_traces()


    ########################
    # Photometry Methods
    ########################
    def _update_main_phot_traces(self, *event):
        # Check if photometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_phot_plots) != 0) and (self.settings_info.lock_trigger == False):
            # If this function was triggered by 'selected_phot_plots', check if the previous value of 'selected_phot_plots' already contained a photometry plot
                # If it did, we should exit the function so that we don't unnecessarily reupdate all photometry traces
                # Currently, this check does nothing since we only have 1 type of photometry plot
            if (event != ()) and (len(event[0].old) != 0):
                return
            else:
                # Check for GP
                if 'GP' not in self.paramztn_info.selected_paramztn:
                    # Reset phot keys
                    self.main_phot_keys = ['non_gp']
                else:
                    selected_params = self.paramztn_info.selected_params
                    mod_param_values = self.settings_info.mod_param_values

                    cel_mod = model.Celerite_GP_Model(self.cache['mod'], 0)
                        
                    # Matern-3/2 parameters
                    log_sig = mod_param_values['gp_log_sigma']

                    if 'gp_rho' in selected_params:
                        log_rho = np.log(mod_param_values['gp_rho'])
                    elif 'gp_log_rho' in selected_params:
                        log_rho = mod_param_values['gp_log_rho']

                    # DDSHO parameters
                    log_Q = np.log(2**-0.5)
                    log_omega0 = mod_param_values['gp_log_omega0']

                    if 'gp_log_S0' in selected_params:
                        log_S0 = mod_param_values['gp_log_S0']
                    elif 'gp_log_omega04_S0' in selected_params:
                        log_S0 = mod_param_values['gp_log_omega04_S0'] - (4 * log_omega0)    
                    elif 'gp_log_omega0_S0' in selected_params:
                        log_S0 = mod_param_values['gp_log_omega0_S0'] - log_omega0

                    # Make fake errors (mimicking OGLE photon noise)
                    flux0 = 4000.0
                    mag0 = 19.0
                    mag_obs = cel_mod.get_value(self.cache['time'])

                    flux_obs = flux0 * 10 ** ((mag_obs - mag0) / -2.5)
                    flux_obs_err = flux_obs ** 0.5
                    mag_obs_err = 1.087 / flux_obs_err

                    # Jitter term parameters
                    if 'gp_log_jit_sigma' in selected_params:
                        log_jit_sigma = mod_param_values['gp_log_jit_sigma']
                    else: 
                        log_jit_sigma = np.log(np.average(mag_obs_err))
                        
                    # Make GP model
                    m32 = celerite.terms.Matern32Term(log_sig, log_rho)
                    sho = celerite.terms.SHOTerm(log_S0, log_Q, log_omega0)
                    jitter = celerite.terms.JitterTerm(log_jit_sigma)
                    kernel = m32 + sho + jitter

                    gp = celerite.GP(kernel, mean = cel_mod, fit_mean = True)
                    gp.compute(self.cache['time'], mag_obs_err)

                    # Update the GP object in cache
                    self.cache['gp'] = gp

                    # Change phot of 'gp_prior' traces. This is done so that we don't have to call 'get_photometry' twice
                    self.phot_traces['gp_prior'].phot = mag_obs

                    # Reset phot keys
                    self.main_phot_keys = ['gp_prior', 'gp_predict', 'gp_samps']

            # Update relevant phot traces
                # Note the 'gp_prior' is excluded because we would have already updated it's photometry
            for trace_key in set(self.main_phot_keys) - {'gp_prior'}:
                trace_thread = threading.Thread(self.all_traces[trace_key]._update_trace())
                trace_thread.start()
            

    def _update_gp_samps(self, *event):
        '''
        This is a function used so that we don't have to recalculate photometry every time the number of GP samples changes
        '''

        # Note: '*event' is needed for 'Num_samps' watcher

        # Check if photometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets and slider resets
        if (len(self.selected_phot_plots) != 0) and (self.settings_info.lock_trigger == False):
            self.all_traces['gp_samps']._update_trace()


    ########################
    # Astrometry Methods
    ######################## 
    def _update_main_ast_traces(self, *event):
        # *event is used for 'selected_ast_plots' dependency

        # Check if astrometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_ast_plots) != 0) and (self.settings_info.lock_trigger == False):
            # If this function was triggered by 'selected_ast_plots', check if the previous value of 'selected_ast_plots' already contained an astronomy plot
                # If it did, we should exit the function so that we don't unnecessarily reupdate all astronomy traces
            if (event != ()) and (len(event[0].old) != 0):
                return
            else:
                selected_paramztn = self.paramztn_info.selected_paramztn
                if 'BL' in selected_paramztn:
                    self.cache['bl_image_arr'], self.cache['bl_amp_arr'] = self.cache['mod'].get_all_arrays(self.cache['time'])

                self.main_ast_keys = ['unres_len', 'unres_unlen']

                # Update relevant ast traces
                for trace_key in self.main_ast_keys:
                    trace_thread = threading.Thread(self.all_traces[trace_key]._update_trace())
                    trace_thread.start()


    @pn.depends('settings_info.ast_checkbox.value', watch = True)
    def _update_extra_ast_traces(self, *event):
        # Check if astrometry is selected in dashboard
        # Check for locks. This is needed to guard against checkbox resets
        if (len(self.selected_ast_plots) != 0) and (self.settings_info.lock_trigger == False):
            # If this function was triggered by 'selected_ast_plots', check if the previous value of 'selected_ast_plots' already contained an astronomy plot
                # If it did, we should exit the function so that we don't unnecessarily reupdate all astronomy traces
            if (event != ()) and (len(event[0].old) != 0):
                return
            else:
                extra_ast_keys = []
                for cb_key in self.settings_info.ast_checkbox.value:
                    extra_ast_keys += self.extra_ast_cb_map[cb_key]
                
                # Update relevant ast traces
                for trace_key in extra_ast_keys:
                    trace_thread = threading.Thread(self.all_traces[trace_key]._update_trace())
                    trace_thread.start()

                self.extra_ast_keys = extra_ast_keys

            # These need to be removed to have the traces properly updating when parameters change
            for key in ['bs_res_unlen', 'bs_res_len']:
                self.cache.pop(key, None)


# Note: For all trace classes, '_update_trace' needs to be called before plotting
    # The purpose of '_update_trace' is to take the output of BAGLE/celerite functions and organize them in a more plottable manner
################################################
# General Photometry Traces
################################################
class Genrl_Phot(param.Parameterized):
    '''
    Note: This is used for non-GP and GP photometry traces
    '''

    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)

    def __init__(self, cache, gp_trace, 
                 group_name, zorder, show_legend,
                 time_width, full_width, marker_size,
                 full_dash_style = 'dash', 
                 pri_clr = None, sec_clr = None, opacity = 1, 
                 **params):
        super().__init__(**params)
        '''
        cache: a dictionary that should be shared across all traces.
        gp_trace: a boolean indicating whether the trace is for GP (True) or non-GP (False).
        '''
        self.cache = cache
        self.gp_trace = gp_trace
        self.group_name, self.zorder, self.show_legend = group_name, zorder, show_legend
        self.time_width, self.marker_size, self.full_width = time_width, marker_size, full_width
        self.full_dash_style = full_dash_style
        self.pri_clr, self.sec_clr, self.opacity = pri_clr, sec_clr, opacity

        self.phot = None
        
        # This is a dictionary to store the indices of all traces using a primary color or a secondary color
        self.all_trace_idx = {}

    def _update_trace(self):
        if self.gp_trace == False:
            self.phot = self.cache['mod'].get_photometry(self.cache['time'])

        else:
            # Get predictive mean
            gp = self.cache['gp']
            mag_obs_corr = gp.sample(size = 1)[0]
            self.phot = gp.predict(mag_obs_corr, return_cov = False)

    def plot_time(self, fig, time_idx):
        self.all_trace_idx['pri_clr'] = [self.cache['current_idx']] # Time trace should reset the 'pri_clr' value
        self.cache['current_idx'] += 1

        fig.add_trace(
            go.Scatter(
                x = self.cache['time'][time_idx],
                y = self.phot[time_idx],
                name = '', 
                zorder = self.zorder,
                legendgroup = self.group_name, 
                showlegend = self.show_legend,
                legendgrouptitle = dict(text = self.group_name, font_size = styles.FONTSIZES['plot_legendgroup']),
                line = dict(color = self.pri_clr, width = self.time_width),
                opacity = self.opacity,
                hovertemplate = styles.ALL_TEMPLATES['phot']
            )
        )

    def plot_full(self, fig):
        self.all_trace_idx['sec_clr'] = [self.cache['current_idx']] # Full trace should reset the 'sec_clr' value
        self.cache['current_idx'] += 1

        fig.add_trace(
            go.Scatter(
                x = self.cache['time'],
                y = self.phot,
                name = '', 
                zorder = -100,
                legendgroup = self.group_name, 
                showlegend = False, 
                line = dict(color = self.sec_clr, width = self.full_width, dash = self.full_dash_style),
                opacity = self.opacity,
                hovertemplate = styles.ALL_TEMPLATES['phot']
            )
        )

    def plot_marker(self, fig, marker_idx):
        self.all_trace_idx['pri_clr'].append(self.cache['current_idx']) # Marker trace should append to the 'pri_clr' value. This assumes markers are plotted after time.
        self.cache['current_idx'] += 1

        fig.add_trace(
            go.Scatter(
                x = [self.cache['time'][marker_idx]],
                y = [self.phot[marker_idx]],
                name = '', zorder = self.zorder,
                legendgroup = self.group_name, 
                showlegend = False,
                mode = 'markers', 
                marker = dict(color = self.pri_clr, size = self.marker_size),
                opacity = self.opacity,
                hoverinfo = 'skip'
            )
        )
    
    def get_phot_list(self):
        return list(self.phot)
    

################################################
# GP Prior Samples
################################################
class Phot_GP_Samps(param.Parameterized):
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)

    def __init__(self, cache, 
                 group_name, 
                 time_width, 
                 clr_cycle = None, opacity = 1,
                 **params):
        '''
        cache: a dictionary that should be shared across all traces.
        '''

        super().__init__(**params)
        self.cache = cache
        self.group_name = group_name
        self.time_width = time_width
        self.clr_cycle, self.opacity = clr_cycle, opacity

        self.samp_list = None

        # The keys of this dictionary are the indices of the color cycle, while the values is a list with the trace indices
        self.all_trace_idx = {}

    def _update_trace(self, *event):
        self.samp_list = self.cache['gp'].sample(size = self.settings_info.param_sliders['Num_samps'].value)
        
    def plot_time(self, fig, time_idx):
        num_samps = self.settings_info.param_sliders['Num_samps'].value
        if num_samps > 0:
            # Color cycle for samples
            # I'm using 'itertools.cycle' here just in case we want to increase the maximum number of samples past 10
            clr_cycle = itertools.cycle(self.clr_cycle)
            
            # Lists used to only show the legend for the first sample and put it in front for visual purposes
            zorder_list = np.repeat(-100, num_samps).tolist()
            show_legend_list = np.repeat(False, num_samps).tolist()
            zorder_list[0], show_legend_list[0] = -99, True
            
            # Reset all_trace_idx lists before plotting
            for cycle_idx in range(len(self.clr_cycle)):
                self.all_trace_idx['clr_cycle', cycle_idx] = []

            for i, samp in enumerate(self.samp_list):
                clr = next(clr_cycle)
                cycle_idx = self.clr_cycle.index(clr)
                self.all_trace_idx['clr_cycle', cycle_idx].append(self.cache['current_idx'])
                self.cache['current_idx'] += 1

                fig.add_trace(
                    go.Scatter(
                        x = self.cache['time'][time_idx],
                        y = samp[time_idx],
                        name = '', 
                        zorder = zorder_list[i],
                        legendgroup = self.group_name, 
                        showlegend = show_legend_list[i],
                        legendgrouptitle = dict(text = self.group_name, font_size = styles.FONTSIZES['plot_legendgroup']),
                        line = dict(color = clr, width = self.time_width),
                        opacity = self.opacity,
                        hoverinfo = 'skip'
                    )
                )

    def get_phot_list(self):
        phot_list = []
        for samp in self.samp_list:
            phot_list += list(samp)
        return phot_list
    

################################################
# Unresolved, Source Astrometry Traces
################################################
class Ast_Unres(param.Parameterized):
    '''
    Note: This is used for all unresolved astrometry (lensed and unlensed)
    '''
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)

    def __init__(self, cache, lensed_trace, 
                 group_name, zorder,
                 time_width, full_width, marker_size, 
                 pri_clr = None, sec_clr = None,
                 **params):
        '''
        cache: a dictionary that should be shared across all traces.
        lensed_trace: a boolean indicating whether the trace is for lensed (True) or unlensed (False) astrometry.
        '''

        super().__init__(**params)
        self.cache = cache
        self.lensed_trace = lensed_trace
        self.group_name, self.zorder = group_name, zorder
        self.time_width, self.marker_size, self.full_width = time_width, marker_size, full_width
        self.pri_clr, self.sec_clr = pri_clr, sec_clr

        # This will be a dictionary storing the x-data, y-data, and text-data for each ast plot type
        self.plot_data = None

        # This is a dictionary to store the indices of all traces using a primary color or a secondary color
        self.all_trace_idx = {}

    def _update_trace(self):
        '''
        This function should separate the outputs of 'get_astrometry_unlensed' or 'get_astrometry' into their RA and Dec arrays.
        The RA and Dec arrays should then be stored in self.plot_data, where they can be accessed by the plotting and get_xy_lists functions.
        '''

        if self.lensed_trace == False:
            ast = self.cache['mod'].get_astrometry_unlensed(self.cache['time'])
            
        else:
            selected_paramztn = self.paramztn_info.selected_paramztn
            if 'PL' in selected_paramztn:
                ast = self.cache['mod'].get_astrometry(self.cache['time'])
            elif 'BL' in selected_paramztn:
                ast = self.cache['mod'].get_astrometry(self.cache['time'], self.cache['bl_image_arr'], self.cache['bl_amp_arr'])

        ra, dec = ast[:, 0], ast[:, 1]

        #  Note: order of tuple is (x_data, y_data, text)
        self.plot_data = {
            'ast_radec': (ra, dec, self.cache['time']),
            'ast_ra': (self.cache['time'], ra, None),
            'ast_dec': (self.cache['time'], dec, None)
        }

    def plot_time(self, fig, plot_name, time_idx):
        self.all_trace_idx['pri_clr'] = [self.cache['current_idx']] # Time trace should reset the 'pri_clr' value
        self.cache['current_idx'] += 1

        fig.add_trace(
            go.Scatter(
                x = self.plot_data[plot_name][0][time_idx],
                y = self.plot_data[plot_name][1][time_idx],
                name = '', 
                zorder = self.zorder,
                legendgroup = self.group_name, 
                showlegend = True,
                legendgrouptitle = dict(text = self.group_name, font_size = styles.FONTSIZES['plot_legendgroup']),
                line = dict(color = self.pri_clr, width = self.time_width),
                hovertemplate = styles.ALL_TEMPLATES[plot_name],
                text = self.plot_data[plot_name][2]
            )
        )

    def plot_full(self, fig, plot_name):
        self.all_trace_idx['sec_clr'] = [self.cache['current_idx']] # Time trace should reset the 'sec_clr' value
        self.cache['current_idx'] += 1

        fig.add_trace(
            go.Scatter(
                x = self.plot_data[plot_name][0],
                y = self.plot_data[plot_name][1],
                name = '', 
                zorder = -100,
                legendgroup = self.group_name, 
                showlegend = False,
                line = dict(color = self.sec_clr, width = self.full_width, dash = 'dash'),
                hovertemplate = styles.ALL_TEMPLATES[plot_name],
                text = self.plot_data[plot_name][2]
            )
        )

    def plot_marker(self, fig, plot_name, marker_idx):
        self.all_trace_idx['pri_clr'].append(self.cache['current_idx']) # Marker trace should append to the 'pri_clr' value. This assumes markers are plotted after time.
        self.cache['current_idx'] += 1

        fig.add_trace(
            go.Scatter(
                x = [self.plot_data[plot_name][0][marker_idx]],
                y = [self.plot_data[plot_name][1][marker_idx]],
                name = '', 
                zorder = self.zorder,
                legendgroup = self.group_name, 
                showlegend = False,
                mode = 'markers', 
                marker = dict(color = self.pri_clr, size = self.marker_size),
                hoverinfo = 'skip'
            )
        )
    
    def get_xy_lists(self, plot_name):
        x_list = list(self.plot_data[plot_name][0])
        y_list = list(self.plot_data[plot_name][1])
        return x_list, y_list        


################################################
# Resolved, Point-Source Astrometry Traces
################################################
class Ast_PS_ResLensed(param.Parameterized):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)

    def __init__(self, cache,
                 group_name,
                 time_width, marker_size, 
                 pri_clr = None,
                 **params):
        '''
        cache: a dictionary that should be shared across all traces.
        '''

        super().__init__(**params)
        self.cache = cache
        self.group_name = group_name
        self.time_width, self.marker_size = time_width, marker_size
        self.pri_clr = pri_clr

        # This will be a dictionary storing the lists of x-data and y-data for each ast plot type
        self.plot_data = None
        self.num_imgs = None
        
        # This is a dictionary to store the indices of all traces using a primary color or a secondary color
        self.all_trace_idx = {}

    def _update_trace(self):
        '''
        This function should separate the outputs of 'get_resolved_astrometry' into their RA and Dec arrays for each source image.
        The RA and Dec arrays should then be stored in self.plot_data, where they can be accessed by the plotting and get_xy_lists functions.
        '''

        ast = self.cache['mod'].get_resolved_astrometry(self.cache['time'])

        ra_list, dec_list = [], []

        # Check if point-lens (2 imgs) or binary-lens (5 imgs)
        selected_paramztn = self.paramztn_info.selected_paramztn
        if 'PL' in selected_paramztn:
            self.num_imgs = 2
            for i in range(2):
                ra_list.append(ast[i][:, 0])
                dec_list.append(ast[i][:, 1])  

        elif 'BL' in selected_paramztn:
            self.num_imgs = 5
            for i in range(5):
                ra_list.append(ast[:, i][:, 0])
                dec_list.append(ast[:, i][:, 1])

        # Repeat time by number of images for easy plotting
        time_list = list(itertools.repeat(self.cache['time'], self.num_imgs))

        # Note: order of tuple is (x_data, y_data)
        self.plot_data = {
            'ast_radec': (ra_list, dec_list),
            'ast_ra': (time_list, ra_list),
            'ast_dec': (time_list, dec_list)
        }

    def plot_time(self, fig, plot_name, time_idx):
        show_legend_list = np.repeat(False, self.num_imgs).tolist()
        show_legend_list[0] = True

        self.all_trace_idx['pri_clr'] = [] # Time trace should reset the 'pri_clr' value before plotting
        for i in range(self.num_imgs):
            self.all_trace_idx['pri_clr'].append(self.cache['current_idx'])
            self.cache['current_idx'] += 1

            fig.add_trace(
                go.Scattergl(
                    x = self.plot_data[plot_name][0][i][time_idx],
                    y = self.plot_data[plot_name][1][i][time_idx],
                    name = '',
                    legendgroup = self.group_name, 
                    showlegend = show_legend_list[i],
                    legendgrouptitle = dict(text = self.group_name, font_size = styles.FONTSIZES['plot_legendgroup']),
                    mode = 'markers', 
                    marker = dict(color = self.pri_clr, size = 1),
                    hoverinfo = 'skip'
                )
            )

    def plot_marker(self, fig, plot_name, marker_idx):
        # zorder = 1000 forces markers to be in the front, which is needed to nearly Scattergl       
        for i in range(self.num_imgs):
            self.all_trace_idx['pri_clr'].append(self.cache['current_idx'])
            self.cache['current_idx'] += 1

            fig.add_trace(
                go.Scatter(
                    x = [self.plot_data[plot_name][0][i][marker_idx]],
                    y = [self.plot_data[plot_name][1][i][marker_idx]],
                    name = '', zorder = 1000,
                    legendgroup = self.group_name, 
                    showlegend = False,
                    mode = 'markers', 
                    marker = dict(color = self.pri_clr, size = self.marker_size),
                    hoverinfo = 'skip'
                )
            )
    
    def get_xy_lists(self, plot_name):
        x_list, y_list = [], []
        # Note: this may unecessarily combine a bunch of repeated time arrays
        for i in range(self.num_imgs):
            x_list += list(self.plot_data[plot_name][0][i])
            y_list += list(self.plot_data[plot_name][1][i])
        return x_list, y_list
    

################################################
# Resolved, Binary-Source Astrometry Traces
################################################
class Ast_BS_ResUnlensed(Ast_Unres):
    def __init__(self, src_idx, *args, **kwargs):
        '''
        src_idx: index of the source. 0 = primary and 1 = secondary.

        Note: this inherits 'Ast_Unres' because it will have a similar plotting style
        '''
        
        super().__init__(*args, **kwargs)
        self.src_idx = src_idx

    def _update_trace(self):
        '''
        This function should separate the outputs of 'get_resolved_astrometry_unlensed' into their RA and Dec arrays for each source.
        The RA and Dec arrays should then be stored in self.plot_data, where they can be accessed by the plotting and get_xy_lists functions.
        '''
        
        if 'bs_res_unlen' not in self.cache:
            # This case implies that we are updating the trace for the first source of the binary pair
            ast = self.cache['mod'].get_resolved_astrometry_unlensed(self.cache['time'])
            self.cache['bs_res_unlen'] = ast
        else:
            # This case implies that 'get_resolved_astrometry_unlensed' was already called through the companion source. 
            # Note: 'bs_res_unlen' will have to be cleared/removed later on in the 'update_extra_ast_traces' function of AllTraces
            ast = self.cache['bs_res_unlen']

        src_ast = ast[:, self.src_idx]
        ra, dec = src_ast[:, 0], src_ast[:, 1]
        
        #  Note: order of tuple is (x_data, y_data, text)
        self.plot_data = {
            'ast_radec': (ra, dec, self.cache['time']),
            'ast_ra': (self.cache['time'], ra, None),
            'ast_dec': (self.cache['time'], dec, None)
        }


class Ast_BS_ResLensed(Ast_PS_ResLensed):
    def __init__(self, src_idx, *args, **kwargs):
        '''
        src_idx: index of the source. 0 = primary and 1 = secondary.

        Note: This inherits 'Ast_PS_ResLensed' because it will have a similar plotting style
        '''

        super().__init__(*args, **kwargs)
        self.src_idx = src_idx
        
        # This will be a dictionary storing the lists of x-data and y-data for each ast plot type
        self.plot_data = None
        self.num_imgs = None

    def _update_trace(self):
        '''
        This function should separate the outputs of 'get_resolved_astrometry' into their RA and Dec arrays for each source and their lensed images.
        The RA and Dec arrays should then be stored in self.plot_data, where they can be accessed by the plotting and get_xy_lists functions.
        '''
        
        # Check if point-lens (2 imgs) or binary-lens (5 imgs)
        selected_paramztn = self.paramztn_info.selected_paramztn
        if 'PL' in selected_paramztn:
            self.num_imgs = 2
        elif 'BL' in selected_paramztn:
            self.num_imgs = 5
        
        if 'bs_res_len' not in self.cache:
            # This case implies that we are updating the trace for the first source of the binary pair
            if 'PL' in selected_paramztn:
                ast = self.cache['mod'].get_resolved_astrometry(self.cache['time'])
            elif 'BL' in selected_paramztn:
                ast = self.cache['mod'].get_resolved_astrometry(self.cache['time'], self.cache['bl_image_arr'], self.cache['bl_amp_arr'])

            self.cache['bs_res_len'] = ast

        else:
            # This case implies that 'get_resolved_astrometry' was already called through the companion source. 
            # Note: 'bs_res_len' will have to be cleared/removed later on in the 'update_extra_ast_traces' function of AllTraces
            ast = self.cache['bs_res_len']

        ra_list, dec_list = [], []
        for i in range(self.num_imgs):
            src_ast = ast[:, self.src_idx, i]
            ra_list.append(src_ast[:, 0])
            dec_list.append(src_ast[:, 1])  
        
        # Repeat time by number of images for easy plotting
        time_list = list(itertools.repeat(self.cache['time'], self.num_imgs))
        
        # Note: order of tuple is (x_data, y_data)
        self.plot_data = {
            'ast_radec': (ra_list, dec_list),
            'ast_ra': (time_list, ra_list),
            'ast_dec': (time_list, dec_list)
        }


################################################
# Lens Astrometry Traces
################################################
class Ast_Lens(param.Parameterized):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)

    def __init__(self, cache,
                 group_name, zorder,
                 time_width, full_width, marker_size, 
                 pri_clr = None, sec_clr = None,
                 **params):
        '''
        cache: a dictionary that should be shared across all traces.
        '''

        super().__init__(**params)
        self.cache = cache
        self.group_name, self.zorder = group_name, zorder
        self.time_width, self.marker_size, self.full_width = time_width, marker_size, full_width
        self.pri_clr, self.sec_clr = pri_clr, sec_clr

        # This will be a dictionary storing the lists of x-data and y-data for each ast plot type
        self.plot_data = None
        self.num_lens = None

        # This is a dictionary to store the indices of all traces using a primary color or a secondary color
        self.all_trace_idx = {}

    def _update_trace(self):
        '''
        This function should separate the outputs of 'get_lens_astrometry' or 'get_resolved_lens_astrometry' into their RA and Dec arrays for each lens.
        The RA and Dec arrays should then be stored in self.plot_data, where they can be accessed by the plotting and get_xy_lists functions.
        '''

        # Check for point-lens or binary-lens
        selected_paramztn = self.paramztn_info.selected_paramztn

        if 'PL' in selected_paramztn:
            ast = self.cache['mod'].get_lens_astrometry(self.cache['time'])
            self.num_lens = 1
            ra_list = [ast[:, 0]]
            dec_list = [ast[:, 1]]
            
        elif 'BL' in selected_paramztn:
            ast = self.cache['mod'].get_resolved_lens_astrometry(self.cache['time'])
            self.num_lens = 2
            ra_list, dec_list = [], []
            for i in range(2):
                ra_list.append(ast[i][:, 0])
                dec_list.append(ast[i][:, 1])

        # Repeat time by number of lenses for easy plotting
        time_list = list(itertools.repeat(self.cache['time'], self.num_lens))

        # Note: order of tuple is (x_data, y_data, text)
        self.plot_data = {
            'ast_radec': (ra_list, dec_list, self.cache['time']),
            'ast_ra': (time_list, ra_list, None),
            'ast_dec': (time_list, dec_list, None)
        }

    def plot_time(self, fig, plot_name, time_idx):
        show_legend_list = np.repeat(False, self.num_lens).tolist()
        show_legend_list[0] = True

        self.all_trace_idx['pri_clr'] = [] # Time trace should reset the 'pri_clr' value before plotting
        for i in range(self.num_lens):
            self.all_trace_idx['pri_clr'].append(self.cache['current_idx'])
            self.cache['current_idx'] += 1

            fig.add_trace(
                go.Scatter(
                    x = self.plot_data[plot_name][0][i][time_idx],
                    y = self.plot_data[plot_name][1][i][time_idx],
                    name = '', 
                    zorder = self.zorder,
                    legendgroup = self.group_name, 
                    showlegend = show_legend_list[i],
                    legendgrouptitle = dict(text = self.group_name, font_size = styles.FONTSIZES['plot_legendgroup']),
                    line = dict(color = self.pri_clr, width = self.time_width),
                    hovertemplate = styles.ALL_TEMPLATES[plot_name],
                    text = self.plot_data[plot_name][2]
                )
            )

    def plot_full(self, fig, plot_name):
        self.all_trace_idx['sec_clr'] = [] # Full trace should reset the 'sec_clr' value before plotting

        for i in range(self.num_lens):
            self.all_trace_idx['sec_clr'].append(self.cache['current_idx'])
            self.cache['current_idx'] += 1

            fig.add_trace(
                go.Scatter(
                    x = self.plot_data[plot_name][0][i],
                    y = self.plot_data[plot_name][1][i],
                    name = '', 
                    zorder = -100,
                    legendgroup = self.group_name, 
                    showlegend = False,
                    line = dict(color = self.sec_clr, width = self.full_width, dash = 'dash'),
                    hovertemplate = styles.ALL_TEMPLATES[plot_name],
                    text = self.plot_data[plot_name][2]
                )
            )

    def plot_marker(self, fig, plot_name, marker_idx):
        for i in range(self.num_lens):
            self.all_trace_idx['pri_clr'].append(self.cache['current_idx'])
            self.cache['current_idx'] += 1
            fig.add_trace(
                go.Scatter(
                    x = [self.plot_data[plot_name][0][i][marker_idx]],
                    y = [self.plot_data[plot_name][1][i][marker_idx]],
                    name = '', 
                    zorder = self.zorder,
                    legendgroup = self.group_name, 
                    showlegend = False,
                    mode = 'markers', 
                    marker = dict(color = self.pri_clr, size = self.marker_size),
                    hoverinfo = 'skip'
                )
            )

    def get_xy_lists(self, plot_name):
        x_list, y_list = [], []
        # Note: this may unecessarily combine a bunch of repeated time arrays
        for i in range(self.num_lens):
            x_list += list(self.plot_data[plot_name][0][i])
            y_list += list(self.plot_data[plot_name][1][i])
        return x_list, y_list