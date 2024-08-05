################################################
# Packages
################################################
import numpy as np
import itertools
import plotly.graph_objects as go

import constants


################################################
# Hover Templates
################################################
PHOT_TEMPLATE = ('<b>Time:</b> %{x:.3f}' +
                 '<br><b>Mag.:</b> %{y:.3f}' +
                 '<extra></extra>')
RADEC_TEMPLATE = ('<b>Time:</b> %{text:.3f}' + 
                  '<br><b><span style="font-size:1rem">&#916;&#120572;</span><sup>*</sup>:</b> %{x:.5f}' +
                  '<br><b><span style="font-size:1rem">&#916;&#120575;</span>:</b> %{y:.5f}' +
                  '<extra></extra>') 
RA_TEMPLATE = ('<b>Time:</b> %{x:.3f}' + 
               '<br><b><span style="font-size:1rem">&#916;&#120572;</span><sup>*</sup>:</b> %{y:.5f}' +
               '<extra></extra>')
DEC_TEMPLATE = ('<b>Time:</b> %{x:.3f}' + 
                '<br><b><span style="font-size:1rem">&#916;&#120575;</span>:</b> %{y:.5f}' +
                '<extra></extra>')

# Dictionary to store templates
ALL_TEMPLATES = {
    'phot': PHOT_TEMPLATE,
    'ast_radec': RADEC_TEMPLATE,
    'ast_ra': RA_TEMPLATE,
    'ast_dec': DEC_TEMPLATE,
}


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
            x = x_limits, y = y_limits,
            marker = dict(color = 'rgba(0, 0, 0, 0)', size = 10),
            mode = 'markers', hoverinfo = 'skip', showlegend = False
        )
    )


# Note: For all trace classes, update_traces needs to be called before plotting
    # The purpose of 'update_traces' is to take the output of BAGLE/celerite functions and organize them in a more plottable manner
    # External functions will have to be used together with update_traces.
################################################
# General Photometry Traces
################################################
class Genrl_Phot:
    '''
    Note: This is used for non-GP and GP photometry traces
    '''
    def __init__(self, group_name, zorder, show_legend,
                 pri_clr, sec_clr,
                 time_width, full_width, marker_size,
                 full_dash_style = 'dash'):
        self.group_name, self.zorder, self.show_legend = group_name, zorder, show_legend
        self.pri_clr, self.sec_clr = pri_clr, sec_clr
        self.time_width, self.marker_size, self.full_width = time_width, marker_size, full_width
        self.full_dash_style = full_dash_style

    def update_traces(self, phot, time):
        '''
        phot: output of 'mod.get_photometry' or 'gp.predict'
        '''
        self.time = time
        self.phot = phot

    def plot_time(self, fig, time_idx):
        fig.add_trace(
            go.Scatter(
                x = self.time[time_idx],
                y = self.phot[time_idx],
                name = '', zorder = self.zorder,
                legendgroup = self.group_name, showlegend = self.show_legend,
                legendgrouptitle = dict(text = self.group_name, 
                                        font_size = constants.FONTSIZES['legendgroup']),
                line = dict(color = self.pri_clr, width = self.time_width),
                hovertemplate = ALL_TEMPLATES['phot']
            )
        )

    def plot_full(self, fig):
        fig.add_trace(
            go.Scatter(
                x = self.time,
                y = self.phot,
                name = '', zorder = -100,
                legendgroup = self.group_name, showlegend = False, 
                line = dict(color = self.sec_clr, width = self.full_width, dash = self.full_dash_style),
                hovertemplate = ALL_TEMPLATES['phot']
            )
        )

    def plot_marker(self, fig, marker_idx):
        fig.add_trace(
            go.Scatter(
                x = [self.time[marker_idx]],
                y = [self.phot[marker_idx]],
                name = '', zorder = self.zorder,
                legendgroup = self.group_name, showlegend = False,
                mode = 'markers', marker = dict(color = self.pri_clr, size = self.marker_size),
                hoverinfo = 'skip'
            )
        )
    
    def get_phot_list(self):
        return list(self.phot)
    

################################################
# GP Prior Samples
################################################
class Phot_GP_Samps:
    def __init__(self, group_name, time_width):
        self.group_name = group_name
        self.time_width = time_width

    def update_traces(self, samp_list, num_samps, time):
        '''
        samp_list: output of 'gp.sample(size = num_samps)'
        '''
        self.time = time
        self.num_samps = num_samps
        self.samp_list = samp_list
        
    def plot_time(self, fig, time_idx):
        if self.num_samps > 0:
            # color cycle for samples
            clr_cycle = itertools.cycle(constants.CLRS['gp_cycle'])
            
            # Lists used to only show the legend for the first sample and put it in front for visual purposes
            zorder_list = np.repeat(-101, self.num_samps).tolist()
            show_legend_list = np.repeat(False, self.num_samps).tolist()
            zorder_list[0], show_legend_list[0] = -100, True
            
            for i, samp in enumerate(self.samp_list):
                fig.add_trace(
                    go.Scatter(
                        x = self.time[time_idx],
                        y = samp[time_idx],
                        name = '', zorder = zorder_list[i],
                        legendgroup = self.group_name, showlegend = show_legend_list[i],
                        legendgrouptitle = dict(text = self.group_name, 
                                                font_size = constants.FONTSIZES['legendgroup']),
                        line = dict(color = next(clr_cycle), width = self.time_width),
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
class Ast_Unres:
    '''
    Note: This is used for all unresolved astrometry (lensed and unlensed)
    '''
    def __init__(self, group_name, zorder,
                 pri_clr, sec_clr,
                 time_width, full_width, marker_size):
        self.group_name, self.zorder = group_name, zorder
        self.pri_clr, self.sec_clr = pri_clr, sec_clr
        self.time_width, self.marker_size, self.full_width = time_width, marker_size, full_width

    def update_traces(self, unres_ast, time):
        '''
        unres_ast: output of 'mod.get_astrometry' or 'mod.get_astrometry_unlensed'

        Note: order of tuple is (x_data, y_data, text)
        '''

        ra, dec = unres_ast[:, 0], unres_ast[:, 1]

        #  Note: order of tuple is (x_data, y_data, text)
        self.plot_data = {
            'ast_radec': (ra, dec, time),
            'ast_ra': (time, ra, None),
            'ast_dec': (time, dec, None)
        }

    def plot_time(self, fig, plot_name, time_idx):
        fig.add_trace(
            go.Scatter(
                x = self.plot_data[plot_name][0][time_idx],
                y = self.plot_data[plot_name][1][time_idx],
                name = '', zorder = self.zorder,
                legendgroup = self.group_name, showlegend = True,
                legendgrouptitle = dict(text = self.group_name, 
                                        font_size = constants.FONTSIZES['legendgroup']),
                line = dict(color = self.pri_clr, width = self.time_width),
                hovertemplate = ALL_TEMPLATES[plot_name],
                text = self.plot_data[plot_name][2]
            )
        )

    def plot_full(self, fig, plot_name):
        fig.add_trace(
            go.Scatter(
                x = self.plot_data[plot_name][0],
                y = self.plot_data[plot_name][1],
                name = '', zorder = -100,
                legendgroup = self.group_name, showlegend = False,
                line = dict(color = self.sec_clr, width = self.full_width, dash = 'dash'),
                hovertemplate = ALL_TEMPLATES[plot_name],
                text = self.plot_data[plot_name][2]
            )
        )

    def plot_marker(self, fig, plot_name, marker_idx):
        fig.add_trace(
            go.Scatter(
                x = [self.plot_data[plot_name][0][marker_idx]],
                y = [self.plot_data[plot_name][1][marker_idx]],
                name = '', zorder = self.zorder,
                legendgroup = self.group_name, showlegend = False,
                mode = 'markers', marker = dict(color = self.pri_clr, size = self.marker_size),
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
class Ast_PS_ResLensed:
    def __init__(self, group_name,
                 pri_clr,
                 time_width, marker_size):
        self.group_name = group_name
        self.pri_clr = pri_clr
        self.time_width, self.marker_size = time_width, marker_size

    def update_traces(self, ps_res_ast, paramztn, time):
        '''
        res_ps_ast: output of 'mod.get_resolved_astrometry'
        '''

        ra_list, dec_list = [], []
        # Check if point-lens (2 imgs) or binary-lens (5 imgs)
        if 'PL' in paramztn:
            self.num_imgs = 2
            for i in range(2):
                ra_list.append(ps_res_ast[i][:, 0])
                dec_list.append(ps_res_ast[i][:, 1])  

        elif 'BL' in paramztn:
            self.num_imgs = 5
            for i in range(5):
                ra_list.append(ps_res_ast[:, i][:, 0])
                dec_list.append(ps_res_ast[:, i][:, 1])

        # Repeat time by number of images for easy plotting
        time_list = list(itertools.repeat(time, self.num_imgs))

        # Note: order of tuple is (x_data, y_data)
        self.plot_data = {
            'ast_radec': (ra_list, dec_list),
            'ast_ra': (time_list, ra_list),
            'ast_dec': (time_list, dec_list)
        }

    def plot_time(self, fig, plot_name, time_idx):
        show_legend_list = np.repeat(False, self.num_imgs).tolist()
        show_legend_list[0] = True

        for i in range(self.num_imgs):
            fig.add_trace(
                go.Scattergl(
                    x = self.plot_data[plot_name][0][i][time_idx],
                    y = self.plot_data[plot_name][1][i][time_idx],
                    name = '',
                    legendgroup = self.group_name, showlegend = show_legend_list[i],
                    legendgrouptitle = dict(text = self.group_name, 
                                            font_size = constants.FONTSIZES['legendgroup']),
                    mode = 'markers', marker = dict(color = self.pri_clr, size = 1),
                    hoverinfo = 'skip'
                )
            )

    def plot_marker(self, fig, plot_name, marker_idx):
        # zorder = 1000 forces markers to be in the front, which is needed to nearly Scattergl       
        for i in range(self.num_imgs):
            fig.add_trace(
                go.Scatter(
                    x = [self.plot_data[plot_name][0][i][marker_idx]],
                    y = [self.plot_data[plot_name][1][i][marker_idx]],
                    name = '', zorder = 1000,
                    legendgroup = self.group_name, showlegend = False,
                    mode = 'markers', marker = dict(color = self.pri_clr, size = self.marker_size),
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

    def update_traces(self, res_unlen_bs_ast, time):
        '''
        res_unlen_bs_ast: output of 'mod.get_resolved_astrometry_unlensed'
        '''
        
        src_ast = res_unlen_bs_ast[:, self.src_idx]
        ra, dec = src_ast[:, 0], src_ast[:, 1]
        
        #  Note: order of tuple is (x_data, y_data, text)
        self.plot_data = {
            'ast_radec': (ra, dec, time),
            'ast_ra': (time, ra, None),
            'ast_dec': (time, dec, None)
        }   

class Ast_BS_ResLensed(Ast_PS_ResLensed):
    def __init__(self, src_idx, *args, **kwargs):
        '''
        src_idx: index of the source. 0 = primary and 1 = secondary.

        Note: This inherits 'Ast_PS_ResLensed' because it will have a similar plotting style
        '''
        super().__init__(*args, **kwargs)
        self.src_idx = src_idx
        
    def update_traces(self, res_bs_ast, paramztn, time):
        '''
        res_bs_ast: output of 'mod.get_resolved_astrometry'
        '''
        
        # Check if point-lens (2 imgs) or binary-lens (5 imgs)
        if 'PL' in paramztn:
            self.num_imgs = 2
        elif 'BL' in paramztn:
            self.num_imgs = 5
        
        ra_list, dec_list = [], []
        for i in range(self.num_imgs):
            src_ast = res_bs_ast[:, self.src_idx, i]
            ra_list.append(src_ast[:, 0])
            dec_list.append(src_ast[:, 1])  
        
        # Repeat time by number of images for easy plotting
        time_list = list(itertools.repeat(time, self.num_imgs))
        
        # Note: order of tuple is (x_data, y_data)
        self.plot_data = {
            'ast_radec': (ra_list, dec_list),
            'ast_ra': (time_list, ra_list),
            'ast_dec': (time_list, dec_list)
        }


################################################
# Lens Astrometry Traces
################################################
class Ast_Lens:
    def __init__(self, group_name, zorder,
                 pri_clr, sec_clr,
                 time_width, full_width, marker_size):
        self.group_name, self.zorder = group_name, zorder
        self.pri_clr, self.sec_clr = pri_clr, sec_clr
        self.time_width, self.marker_size, self.full_width = time_width, marker_size, full_width

    def update_traces(self, lens_ast, paramztn, time):
        '''
        lens_ast: output of 'mod.get_lens_astrometry' or 'mod.get_resolved_lens_astrometry'
        '''

        if 'PL' in paramztn:
            self.num_lens = 1
            ra_list = [lens_ast[:, 0]]
            dec_list = [lens_ast[:, 1]]
            
        elif 'BL' in paramztn:
            self.num_lens = 2
            ra_list, dec_list = [], []
            for i in range(2):
                ra_list.append(lens_ast[i][:, 0])
                dec_list.append(lens_ast[i][:, 1])

        # Repeat time by number of lenses for easy plotting
        time_list = list(itertools.repeat(time, self.num_lens))

        # Note: order of tuple is (x_data, y_data, text)
        self.plot_data = {
            'ast_radec': (ra_list, dec_list, time),
            'ast_ra': (time_list, ra_list, None),
            'ast_dec': (time_list, dec_list, None)
        }

    def plot_time(self, fig, plot_name, time_idx):
        show_legend_list = np.repeat(False, self.num_lens).tolist()
        show_legend_list[0] = True

        for i in range(self.num_lens):
            fig.add_trace(
                go.Scatter(
                    x = self.plot_data[plot_name][0][i][time_idx],
                    y = self.plot_data[plot_name][1][i][time_idx],
                    name = '', zorder = self.zorder,
                    legendgroup = self.group_name, showlegend = show_legend_list[i],
                    legendgrouptitle = dict(text = self.group_name, 
                                            font_size = constants.FONTSIZES['legendgroup']),
                    line = dict(color = self.pri_clr, width = self.time_width),
                    hovertemplate = ALL_TEMPLATES[plot_name],
                    text = self.plot_data[plot_name][2]
                )
            )

    def plot_full(self, fig, plot_name):
        for i in range(self.num_lens):
            fig.add_trace(
                go.Scatter(
                    x = self.plot_data[plot_name][0][i],
                    y = self.plot_data[plot_name][1][i],
                    name = '', zorder = -100,
                    legendgroup = self.group_name, showlegend = False,
                    line = dict(color = self.sec_clr, width = self.full_width, dash = 'dash'),
                    hovertemplate = ALL_TEMPLATES[plot_name],
                    text = self.plot_data[plot_name][2]
                )
            )

    def plot_marker(self, fig, plot_name, marker_idx):
        for i in range(self.num_lens):
            fig.add_trace(
                go.Scatter(
                    x = [self.plot_data[plot_name][0][i][marker_idx]],
                    y = [self.plot_data[plot_name][1][i][marker_idx]],
                    name = '', zorder = self.zorder,
                    legendgroup = self.group_name, showlegend = False,
                    mode = 'markers', marker = dict(color = self.pri_clr, size = self.marker_size),
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