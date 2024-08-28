################################################
# Packages
################################################
import textwrap
import numpy as np

import panel as pn
from panel.viewable import Viewer
import param

from app_utils import indicators, styles, traces
from app_components import paramztn_select, settings_tabs, color_panel


################################################
# Dashboard - Code Panel
################################################
class CodePanel(Viewer):
    paramztn_info = param.ClassSelector(class_ = paramztn_select.ParamztnSelect)
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)
    trace_info = param.ClassSelector(class_ = traces.AllTraceInfo)
    clr_info = param.ClassSelector(class_ = color_panel.ColorPanel)

    
    def __init__(self, **params):
        super().__init__(**params)
        # Dictionary to store extra astrometry trace code functions
        self.extra_ast_code_fns = {
            'ps_res_len': self.get_ps_res_len_code,
            'bs_res_unlen_pri': self.get_bs_res_unlen_code,
            'bs_res_unlen_sec': self.get_bs_res_unlen_code,
            'bs_res_len_pri': self.get_bs_res_len_code,
            'bs_res_len_sec': self.get_bs_res_len_code,
            'lens': self.get_lens_code
        }

        # Variable to store 'Num_samps' slider watcher for wasy unwatching
        self.samps_watcher = None

        self.code_display = pn.widgets.CodeEditor(
            name = 'code_display',
            sizing_mode = 'stretch_both', 
            language = 'python',
            theme = styles.THEMES['code_theme'],
            styles = {'overflow':'visible'},
            disabled = True,
            readonly = True
        )

        self.code_layout = pn.FlexBox(
            self.code_display,
            sizing_mode = 'stretch_both',
            justify_content = 'center',
            align_content = 'center',
            styles = {'background': styles.CLRS['page_secondary'], 
                      'border': f'{styles.CLRS["page_border"]} solid 0.08rem'},
        )
        
        # Set dependencies
        self.settings_info.param_sliders['Num_pts'].param.watch(self._update_code_str, 'value', precedence = 10)

        for error_bool in self.settings_info.errored_state.values():
            error_bool.param.watch(self.set_errored_layout, 'value', precedence = 10)

        for clr_picker in self.clr_info.fig_clr_pickers.values():
            clr_picker.param.watch(self._update_code_str, 'value', precedence = 10)
        
        for trace_key in self.clr_info.trace_clr_pickers.keys():
            for clr_key in self.clr_info.trace_clr_pickers[trace_key].keys():
                # Note: secondary color has a no dependency because I am only plotting the full time trace
                if clr_key == 'pri_clr':
                    clr_picker = self.clr_info.trace_clr_pickers[trace_key]['pri_clr']
                    clr_picker.param.watch(self._update_code_str, 'value', precedence = 10)
                elif clr_key == 'clr_cycle':
                    for clr_picker in self.clr_info.trace_clr_pickers[trace_key]['clr_cycle']:
                        clr_picker.param.watch(self._update_code_str, 'value', precedence = 10)
        
        self.clr_info.theme_dropdown.param.watch(self._update_code_str, 'value', precedence = 10)

    @pn.depends('paramztn_info.selected_paramztn', watch = True)
    def set_samps_dependency(self):
        # Unwatch first if exists
        if self.samps_watcher != None:
            self.settings_info.param_sliders['Num_samps'].param.unwatch(self.samps_watcher)
            self.samps_watcher = None

        if (self.paramztn_info.selected_paramztn != None) and ('GP' in self.paramztn_info.selected_paramztn):
            self.samps_watcher = self.settings_info.param_sliders['Num_samps'].param.watch(self._update_code_str, 'value')


    def set_errored_layout(self, *event):
        if event[0].obj.value == True:
            self.code_layout.objects = [indicators.get_indicator('error')]


    def reset_scroll(self):
        self.code_layout.clear()
        self.code_layout.objects = [self.code_display]


    ################################################
    # Photometry Code
    ################################################
    def get_phot_code(self, fig_clr_dict):
        phot_code = textwrap.dedent(
            f''' 

                ################################################
                # Photometry Data + Basic Plot
                ################################################
                # Basic Photometry Figure
                phot_fig = go.Figure()
                phot_fig.update_xaxes(
                    title = '{styles.ALL_FORMATS["phot"][1][0]}',
                    title_font_size = {styles.FONTSIZES["plot_axes_labels"]},
                    ticks = 'outside', tickformat = '000', 
                    tickcolor = '{fig_clr_dict["ticks"]}', 
                    tickfont_color = '{fig_clr_dict["ticks"]}', 
                    color = '{fig_clr_dict["labels"]}', 
                    gridcolor = '{fig_clr_dict["gridlines"]}', zeroline = False
                )
                phot_fig.update_yaxes(
                    title = '{styles.ALL_FORMATS["phot"][1][1]}',
                    title_font_size = {styles.FONTSIZES["plot_axes_labels"]},
                    ticks = 'outside', tickformat = '000',
                    tickcolor = '{fig_clr_dict["ticks"]}', 
                    tickfont_color = '{fig_clr_dict["ticks"]}', 
                    color = '{fig_clr_dict["labels"]}', 
                    gridcolor = '{fig_clr_dict["gridlines"]}', zeroline = False,
                    autorange = 'reversed'
                )
                phot_fig.update_layout(
                    plot_bgcolor = '{fig_clr_dict["plot_bg"]}', 
                    paper_bgcolor = '{fig_clr_dict["paper_bg"]}', 
                    font_size = {styles.FONTSIZES["plot_axes_ticks"]},
                    legend = dict(grouptitlefont_color = '{fig_clr_dict["labels"]}', itemsizing = 'constant'),
                    margin = dict(l = 60, r = 10, t = 50, b = 20),
                    title = dict(text = '{styles.ALL_FORMATS["phot"][0]}', y = 0.98, 
                                 font = dict(color = '{fig_clr_dict["labels"]}', size = {styles.FONTSIZES["plot_title"]}))
                )

                fig_dict['phot'] = phot_fig
            '''
        )

        phot_code += textwrap.dedent(self.get_main_phot_trace_code())

        # There are currently no extra photometry traces

        return phot_code
    

    def get_main_phot_trace_code(self):
        if 'GP' not in self.paramztn_info.selected_paramztn:
            phot_trace = self.trace_info.all_traces['non_gp']
            trace_code = f'''

                #----------------------------------
                # Non-GP Photometry
                #----------------------------------
                data_dict['phot'] = mod.get_photometry(data_dict['time'])
                phot_fig.add_trace(
                    go.Scatter(
                        x = data_dict['time'], y = data_dict['phot'],
                        name = '', 
                        zorder = {phot_trace.zorder},
                        legendgroup = '{phot_trace.group_name}', 
                        legendgrouptitle = dict(text = '{phot_trace.group_name}', font_size = {styles.FONTSIZES['plot_legendgroup']}),
                        line = dict(color = '{phot_trace.pri_clr}', width = {phot_trace.time_width}),
                        hovertemplate = '{styles.ALL_TEMPLATES['phot']}'
                    )
                )
            '''  

        else:
            selected_params = self.paramztn_info.selected_params
            # Get Matern-3/2 parameters
            log_sig = "mod_params['gp_log_sigma']"

            if 'gp_rho' in selected_params:
                log_rho = "np.log(mod_params['gp_rho'])"
            elif 'gp_log_rho' in selected_params:
                log_rho = "mod_params['gp_log_rho']"

            # DDSHO parameters
            log_Q = "np.log(2**-0.5)"
            log_omega0 = "mod_params['gp_log_omega0']"

            if 'gp_log_S0'in selected_params:
                log_S0 = "mod_params['gp_log_S0']"

            elif 'gp_log_omega04_S0' in selected_params:
                log_S0 = "mod_params['gp_log_omega04_S0'] - (4 * log_omega0)"

            elif 'gp_log_omega0_S0' in selected_params:
                log_S0 = "mod_params['gp_log_omega0_S0'] - log_omega0"
            
            # Jitter term parameters
            if 'gp_log_jit_sigma' in selected_params:
                log_jit_sigma = "mod_params['gp_log_jit_sigma']"
            else: 
                log_jit_sigma = "np.log(np.average(mag_obs_err))"

            prior_trace = self.trace_info.all_traces['gp_prior']
            pred_trace = self.trace_info.all_traces['gp_predict']
            trace_code = textwrap.dedent(f'''
                # Celerite Model
                cel_mod = model.Celerite_GP_Model(mod, 0)

                # Get Matern-3/2 GP Parameters
                    # Note: log = Natural Logarithm
                log_sig = {log_sig}
                log_rho = {log_rho}

                # Get DDSHO GP parameters
                    # Note: log = Natural Logarithm
                log_Q = {log_Q}
                log_omega0 = {log_omega0}
                log_S0 = {log_S0}

                # Make fake errors (mimicking OGLE photon noise)
                flux0 = 4000.0
                mag0 = 19.0
                mag_obs = cel_mod.get_value(data_dict['time'])

                flux_obs = flux0 * 10 ** ((mag_obs - mag0) / -2.5)
                flux_obs_err = flux_obs ** 0.5
                mag_obs_err = 1.087 / flux_obs_err

                # Make GP model
                m32 = celerite.terms.Matern32Term(log_sig, log_rho)
                sho = celerite.terms.SHOTerm(log_S0, log_Q, log_omega0)
                jitter = celerite.terms.JitterTerm({log_jit_sigma})
                kernel = m32 + sho + jitter

                gp = celerite.GP(kernel, mean = cel_mod, fit_mean = True)
                gp.compute(data_dict['time'], mag_obs_err)

                # Make fake photometry data for prior mean of GP
                mag_obs_corr = gp.sample(size = 1)[0]
                

                #----------------------------------
                # GP Prior Mean
                #----------------------------------
                    # Note: mag_obs = mod.get_photometry(time) from a nonGP, PSPL model
                data_dict['gp_prior_mean'] = mag_obs
                phot_fig.add_trace(
                    go.Scatter(
                        x = data_dict['time'],
                        y = data_dict['gp_prior_mean'],
                        name = '',
                        zorder = {prior_trace.zorder},
                        legendgrouptitle = dict(text = 'GP Prior Mean', font_size = {styles.FONTSIZES['plot_legendgroup']}),
                        line = dict(color = '{prior_trace.pri_clr}', width = {prior_trace.time_width}),
                        hovertemplate = '{styles.ALL_TEMPLATES['phot']}'
                    )
                )
                

                #----------------------------------
                # GP Predictive Mean
                #----------------------------------
                data_dict['gp_predict_mean'] = gp.predict(mag_obs_corr, return_cov = False)
                phot_fig.add_trace(
                    go.Scatter(
                        x = data_dict['time'], y = data_dict['gp_predict_mean'],
                        name = '',
                        zorder = {pred_trace.zorder},
                        legendgrouptitle = dict(text = 'GP Predictive Mean', font_size = {styles.FONTSIZES['plot_legendgroup']}),
                        line = dict(color = '{pred_trace.pri_clr}', width = {pred_trace.time_width}),
                        hovertemplate = '{styles.ALL_TEMPLATES['phot']}'
                    )
                )
            ''')

            num_samps = self.settings_info.param_sliders['Num_samps'].value
            if num_samps > 0:
                samp_trace = self.trace_info.all_traces['gp_samps']
                samp_trace_code = f'''
                    
                    #----------------------------------
                    # GP Samples
                    #----------------------------------
                    num_samps = {num_samps}

                    # Shape is [GP sample, time]
                    data_dict['gp_samps'] = gp.sample(size = num_samps)

                    clr_cycle = itertools.cycle({samp_trace.clr_cycle})
                    zorder_list = np.repeat(-100, num_samps).tolist()
                    show_legend_list = np.repeat(False, num_samps).tolist()
                    zorder_list[0], show_legend_list[0] = -99, True

                    # Loop through GP samples
                    for i, samp in enumerate(data_dict['gp_samps']):
                        clr = next(clr_cycle)
                        phot_fig.add_trace(
                            go.Scatter(
                                x = data_dict['time'],
                                y = samp,
                                name = '', 
                                zorder = zorder_list[i],
                                legendgroup = '{samp_trace.group_name}', 
                                showlegend = show_legend_list[i],
                                legendgrouptitle = dict(text = '{samp_trace.group_name}', font_size = {styles.FONTSIZES['plot_legendgroup']}),
                                line = dict(color = clr, width = {samp_trace.time_width}),
                                opacity = {samp_trace.opacity},
                                hoverinfo = 'skip'
                            )
                        )
                '''
                trace_code += textwrap.dedent(samp_trace_code)

        return trace_code


    ################################################
    # Astrometry Code
    ################################################
    def get_ast_code(self, fig_clr_dict):
        ast_code = textwrap.dedent(
            f''' 

                ################################################
                # Astrometry Data + Basic Figure (RA vs. Dec)
                ################################################
                # Basic Astrometry Figure (RA vs. Dec)
                ast_fig = go.Figure()
                ast_fig.update_xaxes(
                    title = '{styles.ALL_FORMATS["ast_radec"][1][0]}',
                    title_font_size = {styles.FONTSIZES["plot_axes_labels"]},
                    ticks = 'outside', tickformat = '000', 
                    tickcolor = '{fig_clr_dict["ticks"]}', 
                    tickfont_color = '{fig_clr_dict["ticks"]}', 
                    color = '{fig_clr_dict["labels"]}', 
                    gridcolor = '{fig_clr_dict["gridlines"]}', zeroline = False
                )
                ast_fig.update_yaxes(
                    title = '{styles.ALL_FORMATS["ast_radec"][1][1]}',
                    title_font_size = {styles.FONTSIZES["plot_axes_labels"]},
                    ticks = 'outside', tickformat = '000',
                    tickcolor = '{fig_clr_dict["ticks"]}', 
                    tickfont_color = '{fig_clr_dict["ticks"]}', 
                    color = '{fig_clr_dict["labels"]}', 
                    gridcolor = '{fig_clr_dict["gridlines"]}', zeroline = False
                )
                ast_fig.update_layout(
                    plot_bgcolor = '{fig_clr_dict["plot_bg"]}', 
                    paper_bgcolor = '{fig_clr_dict["paper_bg"]}', 
                    font_size = {styles.FONTSIZES["plot_axes_ticks"]},
                    legend = dict(grouptitlefont_color = '{fig_clr_dict["labels"]}', itemsizing = 'constant'),
                    margin = dict(l = 60, r = 10, t = 50, b = 20),
                    title = dict(text = '{styles.ALL_FORMATS["ast_radec"][0]}', y = 0.98, 
                                 font = dict(color = '{fig_clr_dict["labels"]}', size = {styles.FONTSIZES["plot_title"]}))
                )

                fig_dict['ast'] = ast_fig
            '''
        )

        ast_code += textwrap.dedent(self.get_main_ast_trace_code())
        ast_code += textwrap.dedent(self.get_extra_ast_trace_code())

        return ast_code
    
    def get_main_ast_trace_code(self):
        unres_unlen_trace = self.trace_info.all_traces['unres_unlen']
        unres_len_trace = self.trace_info.all_traces['unres_len']
        trace_code = f'''

            #----------------------------------
            # Unresolved, Unlensed Source(s)
            #----------------------------------
            # Shape is [time, RA/Dec]
            data_dict['unres_unlen_src'] = mod.get_astrometry_unlensed(data_dict['time'])
            ast_fig.add_trace(
                go.Scatter(
                    x = data_dict['unres_unlen_src'][:, 0],
                    y = data_dict['unres_unlen_src'][:, 1],
                    name = '', 
                    zorder = {unres_unlen_trace.zorder},
                    legendgroup = '{unres_unlen_trace.group_name}', 
                    legendgrouptitle = dict(text = '{unres_unlen_trace.group_name}', font_size = {styles.FONTSIZES["plot_legendgroup"]}),
                    line = dict(color = '{unres_unlen_trace.pri_clr}', width = {unres_unlen_trace.time_width}),
                    hovertemplate = '{styles.ALL_TEMPLATES["ast_radec"]}',
                    text = data_dict['time']
                )
            )


            #----------------------------------
            # Unresolved, Lensed Source(s)
            #----------------------------------
            # Shape is [time, RA/Dec]
            data_dict['unres_len_src'] = mod.get_astrometry(data_dict['time'])
            ast_fig.add_trace(
                go.Scatter(
                    x = data_dict['unres_len_src'][:, 0],
                    y = data_dict['unres_len_src'][:, 1],
                    name = '', 
                    zorder = {unres_len_trace.zorder},
                    legendgroup = '{unres_len_trace.group_name}', 
                    legendgrouptitle = dict(text = '{unres_len_trace.group_name}', font_size = {styles.FONTSIZES["plot_legendgroup"]}),
                    line = dict(color = '{unres_len_trace.pri_clr}', width = {unres_len_trace.time_width}),
                    hovertemplate = '{styles.ALL_TEMPLATES["ast_radec"]}',
                    text = data_dict['time']
                )
            )
        '''

        return trace_code

    def get_extra_ast_trace_code(self):
        extra_ast_trace_keys = self.trace_info.extra_ast_keys.copy()

        if {'bs_res_unlen_pri', 'bs_res_unlen_sec'} <= set(extra_ast_trace_keys):
            # remove the secondary source key to prevent having repeated data code
            extra_ast_trace_keys.remove('bs_res_unlen_sec')

        if {'bs_res_len_pri', 'bs_res_len_sec'} <= set(extra_ast_trace_keys):
            # remove the secondary source key to prevent having repeated data code
            extra_ast_trace_keys.remove('bs_res_len_sec')

        trace_code = ''''''
        for trace_key in extra_ast_trace_keys:
            trace_code += textwrap.dedent(self.extra_ast_code_fns[trace_key]())

        return trace_code
    
    def get_ps_res_len_code(self):
        selected_paramztn = self.paramztn_info.selected_paramztn
        if 'PL' in selected_paramztn:
            num_imgs = 2
            shape_str = '# For PSPL, shape is [image, time, RA/Dec]'
            data_str = "data_dict['res_len_src_imgs'][i]"

        elif 'BL' in selected_paramztn:
            num_imgs = 5
            shape_str = '# For PSBL, shape is [time, image, RA/Dec]'
            data_str = "data_dict['res_len_src_imgs'][:, i]"
        
        trace = self.trace_info.all_traces['ps_res_len']
        trace_code = f'''

            #----------------------------------
            # Resolved, Lensed Source Images
            #----------------------------------
            {shape_str}
            data_dict['res_len_src_imgs'] = mod.get_resolved_astrometry(data_dict['time'])
            
            num_imgs = {num_imgs}
            show_legend_list = np.repeat(False, num_imgs).tolist()
            show_legend_list[0] = True

            # Loop through number of images per source
            for i in range(num_imgs):
                ast_fig.add_trace(
                    go.Scattergl(
                        x = {data_str}[:, 0],
                        y = {data_str}[:, 1],
                        name = '',
                        legendgroup = '{trace.group_name}', 
                        showlegend = show_legend_list[i],
                        legendgrouptitle = dict(text = '{trace.group_name}', font_size = {styles.FONTSIZES["plot_legendgroup"]}),
                        mode = 'markers', 
                        marker = dict(color = '{trace.pri_clr}', size = 1),
                        hoverinfo = 'skip'
                    )
                )
        '''

        return trace_code
    
    def get_bs_res_unlen_code(self):
        pri_trace = self.trace_info.all_traces['bs_res_unlen_pri']
        sec_trace = self.trace_info.all_traces['bs_res_unlen_sec']
        trace_code = f'''

        #----------------------------------
        # Resolved, Unlensed Sources
        #----------------------------------
        # Shape is [time, source, RA/Dec]
        data_dict['res_unlen_src'] = mod.get_resolved_astrometry_unlensed(data_dict['time'])

        group_names = ['{pri_trace.group_name}', '{sec_trace.group_name}']
        clrs = ['{pri_trace.pri_clr}', '{sec_trace.pri_clr}']
        widths = [{pri_trace.time_width}, {sec_trace.time_width}]

        # Loop through number sources
        for i in range(2):
            ast_fig.add_trace(
                go.Scatter(
                    x = data_dict['res_unlen_src'][:, i, 0],
                    y = data_dict['res_unlen_src'][:, i, 1],
                    name = '', 
                    zorder = {pri_trace.zorder},
                    legendgroup = group_names[i], 
                    legendgrouptitle = dict(text = group_names[i], font_size = {styles.FONTSIZES["plot_legendgroup"]}),
                    line = dict(color = clrs[i], width = widths[i]),
                    hovertemplate = '{styles.ALL_TEMPLATES["ast_radec"]}',
                    text = data_dict['time']
                )
            )
        '''

        return trace_code

    def get_bs_res_len_code(self):
        extra_ast_trace_keys = self.trace_info.extra_ast_keys
        selected_paramztn = self.paramztn_info.selected_paramztn

        if 'PL' in selected_paramztn:
            num_imgs = 2
        elif 'BL' in selected_paramztn:
            num_imgs = 5
        
        group_names, clrs = [], []
        if 'bs_res_len_pri' in extra_ast_trace_keys:
            pri_trace = self.trace_info.all_traces['bs_res_len_pri']
            group_names.append(pri_trace.group_name)
            clrs.append(pri_trace.pri_clr)
        if 'bs_res_len_sec' in extra_ast_trace_keys:
            sec_trace = self.trace_info.all_traces['bs_res_len_sec']
            group_names.append(sec_trace.group_name)
            clrs.append(sec_trace.pri_clr)

        trace_code = f'''

        #----------------------------------
        # Resolved, Lensed Source Images
        #----------------------------------
        # For binary-source models, shape is [time, source, image, RA/Dec]
        data_dict['res_len_src_imgs'] = mod.get_resolved_astrometry(data_dict['time'])

        num_imgs = {num_imgs}
        group_names = {group_names}
        clrs = {clrs}

        show_legend_list = np.repeat(False, num_imgs).tolist()
        show_legend_list[0] = True

        # Loop through number of sources selected for images
        for i in range(len(group_names)):
            # Loop through number of images per source
            for j in range(num_imgs):
                ast_fig.add_trace(
                    go.Scattergl(
                        x = data_dict['res_len_src_imgs'][:, i, j, 0],
                        y = data_dict['res_len_src_imgs'][:, i, j, 1],
                        name = '',
                        legendgroup = group_names[i], 
                        showlegend = show_legend_list[j],
                        legendgrouptitle = dict(text = group_names[i], font_size = {styles.FONTSIZES["plot_legendgroup"]}),
                        mode = 'markers', 
                        marker = dict(color = clrs[i], size = 1),
                        hoverinfo = 'skip'
                    )
                )
        '''

        return trace_code

    def get_lens_code(self):
        selected_paramztn = self.paramztn_info.selected_paramztn
        trace = self.trace_info.all_traces['lens']

        if 'PL' in selected_paramztn:
            num_lens = 1
            trace_code = textwrap.dedent('''
                                         
                #----------------------------------
                # Point-Lens Astrometry
                #----------------------------------
                # Shape is [time, RA/Dec]
                data_dict['lens_ast'] = mod.get_lens_astrometry(data_dict['time'])
            ''')
            data_str = "data_dict['lens_ast']"
        elif 'BL' in selected_paramztn:
            num_lens = 2
            trace_code = textwrap.dedent('''

                #----------------------------------
                # Binary-Lens Astrometry
                #----------------------------------
                # Shape is [lens, time, RA/Dec]
                data_dict['lens_ast'] = mod.get_resolved_lens_astrometry(data_dict['time'])
            ''')
            data_str = "data_dict['lens_ast'][i]"

        trace_code += textwrap.dedent(f'''
            num_lens = {num_lens}

            show_legend_list = np.repeat(False, num_lens).tolist()
            show_legend_list[0] = True

            # Loop through number of lenses
            for i in range(num_lens):
                ast_fig.add_trace(
                    go.Scatter(
                        x = {data_str}[:, 0],
                        y = {data_str}[:, 1],
                        name = '', 
                        zorder = {trace.zorder},
                        legendgroup = '{trace.group_name}', 
                        showlegend = show_legend_list[i],
                        legendgrouptitle = dict(text = '{trace.group_name}', font_size = {styles.FONTSIZES["plot_legendgroup"]}),
                        line = dict(color = '{trace.pri_clr}', width = {trace.time_width}),
                        hovertemplate = '{styles.ALL_TEMPLATES["ast_radec"]}',
                        text = data_dict['time']
                    )
                )
        ''')

        return trace_code


    ################################################
    # Main Code
    ################################################
    @pn.depends('settings_info.trigger_param_change', 'settings_info.dashboard_checkbox.value',
                'settings_info.phot_checkbox.value', 'settings_info.ast_checkbox.value', watch = True)
    def _update_code_str(self, *event):
        # Check if code panel is displayed.
        # Check if lock is on.
        if 'code' in self.settings_info.dashboard_checkbox.value:
            if (self.settings_info.lock_trigger == False) and (self.clr_info.lock_trigger == False):
                print('CODE CHANGED')
                # Code to import packages
                package_code = '''
                    ################################################
                    # Packages
                    ################################################
                    import numpy as np
                    import itertools
                    import plotly.graph_objects as go
                    
                    from bagle import model
                    
                    # Note: celerite is only used for Gaussian Process
                    import celerite
                '''
                
                # Code to instantiate the BAGLE model
                mod_params_str = ''''''
                mod_param_values = self.settings_info.mod_param_values

                for i, key in enumerate(mod_param_values.keys()):
                    value = np.round(mod_param_values[key], 5)

                    if i != len(mod_param_values.keys()) - 1:
                        comma = ','
                    else:
                        comma = ''

                    if key in self.paramztn_info.selected_phot_params:
                        key_value = f''''{key}': np.array({value}){comma}
                        '''
                    else:
                        key_value = f''''{key}': {value}{comma}
                        '''
                    mod_params_str += key_value


                min_t = self.settings_info.param_sliders['Time'].start
                max_t = self.settings_info.param_sliders['Time'].end
                num_pts = self.settings_info.param_sliders['Num_pts'].value

                mod_time_code = f'''

                    ################################################
                    # Model and Time
                    ################################################
                    paramztn_str = '{self.paramztn_info.selected_paramztn}'
                    mod_params = {{
                        {mod_params_str}}}  

                    # Instantiate BAGLE model
                    mod = getattr(model, paramztn_str)(**mod_params)

                    # Dictionary to store data
                    data_dict = {{}}

                    # Dictionary to store figures
                    fig_dict = {{}}

                    # Time points
                    data_dict['time'] = np.linspace({min_t}, {max_t}, {num_pts})
                '''

                code_list = [package_code, mod_time_code]
                

                # Create figure color dictionary
                fig_clr_dict = {key:self.clr_info.fig_clr_pickers[key].value for key in self.clr_info.fig_clr_pickers.keys()}

                # Check if photometry is selected in dashboard
                if (len(self.trace_info.selected_phot_plots) != 0):
                    code_list.append(self.get_phot_code(fig_clr_dict))

                # Check if astrometry is selected in dashboard
                if (len(self.trace_info.selected_ast_plots) != 0):
                    code_list.append(self.get_ast_code(fig_clr_dict))

                py_code = ''
                for code in code_list:
                    py_code += textwrap.dedent(code)
                
                # Add small note on where data and figrues are stored
                py_code += textwrap.dedent('''
                                           
                    ################################################
                    # Accessing Data and Figures
                    ################################################
                    # Data can be accessed through the dictionary: data_dict
                    # Figures can be accessed through the dictionary: fig_dict
                                           
                    # To see the what data and figures are available, use the .keys() method of dictionaries.
                ''')

                # Check if loading/error indicator is displayed
                if self.code_layout.objects[0].name != self.code_display.name:
                    # Check if error exists
                    if True not in [error.value for error in self.settings_info.errored_state.values()]:
                        self.code_layout.objects = [self.code_display]

                self.code_display.value = py_code

    def __panel__(self):
        return self.code_layout
