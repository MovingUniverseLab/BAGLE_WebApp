################################################
# Packages
################################################
import panel as pn


###########################################
# Fonts
###########################################
HTML_FONTFAMILY = 'Helvetica'

# Dictionary for font sizes
FONTSIZES = {
    'page_title':' 2.6rem',
    'page_header': '1.4rem',
    'error_paramztn': '1.2rem',
    'dropdown': '0.75rem',
    'plus': '0.8rem',
    'btn': '0.75rem',
    'slider': '0.8rem',
    'tabltr_title': '0.8rem',
    'tabltr_txt': '0.8rem',
    'checkbox_title': '1.2rem',
    'checkbox_txt': '0.7rem',
    'tabs_txt': '0.8rem',
    'error_tabs_title': '1.5rem',
    'error_tabs_txt': '1.2rem',
    'tooltip': '0.7rem',
    'summary_txt': '0.95rem',
    'plot_axes_ticks': 10,
    'plot_axes_labels': 14,
    'plot_title': 18,
    'plot_legendgroup': 9,
    'clr_picker_header': '0.75rem',
    'clr_type_label': '0.58rem',
    'accordion_header': '1.15rem',
}


###########################################
# General Colors and Themes (Non-Plots)
###########################################
THEMES = {
    'page_theme': 'dark',
    'page_design': 'bootstrap',
    'slider_design': pn.theme.Material,
    'code_theme': 'tomorrow_night_eighties',
}

# The colors chosen match the dark theme of Panel
    # Note: the color picker for Panel only takes in hexadecimals
CLRS = {
    'page_primary': '#121212',
    'page_secondary': '#2b3035',
    'page_tertiary': '#4d4d4d',
    'page_light': '#4bffef',
    'page_selected': '#65afe9',
    'page_border': '#ffffff',
    'txt_primary': '#ffffff',
    'txt_secondary': '#cccccc',
    'error_primary': '#ff0000',
    'error_secondary': '#b30059',
    'summary_vector': '#999999',
    'float_header': '#212529'
}


###########################################
# CSS Styles and Stylesheets (Non-Plots)
###########################################
# Page Raw CSS
# This is mainly used to change the CSS of components that can't be accessed through styles or stylesheets
PAGE_RAW_CSS = f'''
    :host(.card-title) h3 {{
        font-size: {FONTSIZES['accordion_header']} !important;
    }}
    :host .accordion-header {{
        border: {CLRS['page_border']} solid 0.02rem !important;
    }}
'''

# CSS stylesheet for drop down menus
DROPDOWN_STYLESHEET = f'''
    select.bk-input {{
        background-color: {CLRS['page_secondary']};
        color: {CLRS['txt_primary']};
        font-size: {FONTSIZES['dropdown']};
        text-align: center;
        border: {CLRS['page_border']} solid 0.08rem;
        padding-top: 0rem;
        padding-bottom: 0rem;
    }}
'''

# CSS stylesheet for push buttons
BASE_BTN_STYLESHEET = f'''
    :host {{
        --design-primary-color: {CLRS['page_secondary']};
        margin: 0.4rem;
        flex-grow: 1;
    }}
    
    :host(.solid) .bk-btn {{
        color: {CLRS['txt_primary']};
        border: {CLRS['page_border']} solid 0.08rem;
        border-radius: 0.8rem;
        font-size: {FONTSIZES['btn']};
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    }} 
    
    :host(.solid) .bk-btn:hover {{
        color: {CLRS['page_light']};
        border-color: {CLRS['page_light']};
    }}
'''

SELECTED_BTN_STYLESHEET = f'''
    :host {{
        --design-primary-color: {CLRS['page_primary']};
        margin: 0.4rem;
        flex-grow: 1;
    }}
    
    :host(.solid) .bk-btn {{
        color: {CLRS['page_selected']};
        border: {CLRS['page_selected']} solid 0.08rem;
        border-radius: 0.8rem;
        font-size: {FONTSIZES['btn']};
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    }} 
'''

# CSS stylesheet for sliders
BASE_SLIDER_STYLESHEET = f'''
    :host {{
        --design-primary-color: {CLRS['page_light']};
        --design-secondary-color: {CLRS['page_primary']};
    }}
    
    .bk-slider-title {{
        color: {CLRS['txt_primary']};
        font-size: {FONTSIZES['slider']};
    }}
'''

ERRORED_SLIDER_STYLESHEET = f'''
    :host {{
        --design-primary-color: {CLRS['error_primary']};
        --design-secondary-color: {CLRS['page_primary']};
    }}
    
    .bk-slider-title {{
        color: {CLRS['error_primary']};
        font-size: {FONTSIZES['slider']};
    }}
'''

# CSS stylesheet for tabulator
TABLTR_STYLESHEET = f'''
    .tabulator-col-title {{
        font-size: {FONTSIZES['tabltr_title']};
    }}
    
    .tabulator-cell {{
        font-size: {FONTSIZES['tabltr_txt']};
    }}

    .pnx-tabulator {{
        border: {CLRS['page_border']} solid 0.08rem !important;
    }}
'''

# CSS stylesheet for tabs
BASE_TABS_STYLESHEET = f'''
    .bk-tab {{
        color: {CLRS['txt_primary']};
    }}
    
    .bk-tab.bk-active {{
        font-weight: bold;
        color: {CLRS['page_selected']} !important;
        background-color: {CLRS['page_secondary']} !important;
        border-color: {CLRS['page_border']} !important;
    }}
'''

ERRORED_TABS_STYLESHEET = f'''
    .bk-tab {{
        color: {CLRS['error_primary']};
    }}
    
    .bk-tab.bk-active {{
        font-weight: bold;
        color: {CLRS['error_primary']} !important;
        background-color: {CLRS['page_secondary']} !important;
        border-color: {CLRS['error_primary']} !important;
    }}
'''

CONFIRM_BTN_STYLESHEET = f'''
    :host {{
        --design-primary-color: {CLRS['page_primary']};
        margin: 0.4rem;
        flex-grow: 1;
    }}
    
    :host(.solid) .bk-btn {{
        color: {CLRS['txt_primary']};
        border: {CLRS['page_border']} solid 0.08rem;
        border-radius: 0.8rem;
        font-size: {FONTSIZES['btn']};
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    }} 

    :host(.solid) .bk-btn:hover {{
        color: {CLRS['page_light']};
        border-color: {CLRS['page_light']};
    }}
'''

ACCORDION_STYLESHEET = f'''
    :host {{
        --design-background-color: {CLRS['page_secondary']}
    }}
'''

COLOR_PICKER_STYLES = {
    'width': '46%',
    'height': '35px',
    'margin': '1%',
    'margin-left':'2%',
    'margin-right':'2%'
}

COLOR_PICKER_STYLESHEET = f'''
    input.bk-input {{
        background-color: {CLRS['page_secondary']};
        border: {CLRS['page_border']} solid 0.02rem;
    }}
'''

SWITCH_STYLESHEET = f'''
    .body .knob {{
        background-color: {CLRS['page_tertiary']};
    }}
'''

################################################
# Plot Formats/Templates
################################################
# CSS styles
PLOT_WIDTH = 49.75 # plot width in percentage

BASE_PLOTBOX_STYLES = {
    'background': CLRS['page_secondary'],
    'border': f'{CLRS["page_border"]} solid 0.08rem', 
    'height': '100%',
    'width': f'{PLOT_WIDTH}%',
    'flex-shrink': '0',
    'overflow': 'hidden'
}

EXPANDED_PLOTBOX_STYLES = {
    'background': CLRS['page_secondary'],
    'border': f'{CLRS["page_border"]} solid 0.08rem', 
    'height': '100%',
    'width': '100%',
    'flex-shrink': '0',
    'overflow': 'hidden'
}


# Hover Templates
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


# Figure titles
PHOT_TITLE = 'Photometry'
RADEC_TITLE = '&#916;&#120575; vs. &#916;&#120572;</span><sup>*</sup> (Astrometry)'
RA_TITLE = '&#916;&#120572;</span><sup>*</sup> vs. Time (Astrometry)'
DEC_TITLE = '&#916;&#120575; vs. Time (Astrometry)'

# Figure axis labels
    # Note: order of list is (x-axis label, y-axis label)
PHOT_XY = ('Time [MJD]', 'Magnotude [mag]')
RADEC_XY = ('&#916;&#120572;</span><sup>*</sup> [arcsec]', '&#916;&#120575; [arcsec]')
RA_XY = ('Time [MJD]', '&#916;&#120575; [arcsec]')
DEC_XY = ('Time [MJD]', '&#916;&#120575; [arcsec]')

# Plot formating dictionary for plot panes
    # Note: order of list is (Figure Titles, Figure Axis Labels)
ALL_FORMATS = {
    'phot': (PHOT_TITLE, PHOT_XY),
    'ast_radec': (RADEC_TITLE, RADEC_XY),
    'ast_ra': (RA_TITLE, RA_XY),
    'ast_dec': (DEC_TITLE, DEC_XY)
}

# Get dictionary keys for photometry and astrometry plots
def get_plot_names():
    phot_names, ast_names = [], []
    for key in ALL_FORMATS.keys():
        if 'phot' in key:
            phot_names.append(key)
        elif 'ast' in key:
            ast_names.append(key)

    return phot_names, ast_names

PHOT_PLOT_NAMES, AST_PLOT_NAMES = get_plot_names()
ALL_PLOT_NAMES = PHOT_PLOT_NAMES + AST_PLOT_NAMES


################################################
# Plot Themes
################################################
# Maybe change this to remove nested dictionary?
DARK_PLOT_THEME = {
    'plot_bg': '#2b3035',
    'paper_bg': '#2b3035',
    'ticks': '#ffffff',
    'labels': '#ffffff',
    'gridlines': '#666666',

    'non_gp': {
        'pri_clr': '#ff0000', 
        'sec_clr': '#ff4d4d'
        },
    'gp_prior': {
        'pri_clr': '#ffa500', 
        'sec_clr': '#ffc14d'
    },
    'gp_predict': {
        'pri_clr': '#ff0000', 
        'sec_clr': '#ff4d4d'
    },
    'gp_samps': {
        'clr_cycle': ['#22ffa7', '#f6f926', '#eea6fb', '#c9fbe5', '#00b5f7', 
                      '#e3ee9e', '#fc6955', '#86ce00', '#6e899c', '#0f8508'],
    },

    'unres_len': {
        'pri_clr': '#ff0000', 
        'sec_clr': '#ff4d4d'
    },
    'unres_unlen': {
        'pri_clr': '#ffa500', 
        'sec_clr': '#ffc14d'
    },
    'ps_res_len': {
        'pri_clr': '#ffff00'
    },
    'bs_res_unlen_pri': {
        'pri_clr': '#008695', 
        'sec_clr': '#00b8cc'
    },
    'bs_res_unlen_sec': {
        'pri_clr': '#28793e', 
        'sec_clr': '#33994e'
    },
    'bs_res_len_pri': {
        'pri_clr': '#80f2ff'
    },
    'bs_res_len_sec': {
        'pri_clr': '#00cc96'
    },

    'lens': {
        'pri_clr': '#94346e', 
        'sec_clr': '#ca68a3'
    }
}

LIGHT_PLOT_THEME = {
    'plot_bg': '#f7f7f7',
    'paper_bg': '#ffffff',
    'ticks': '#000000',
    'labels': '#000000',
    'gridlines': '#d1d1d1',

    'non_gp': {
        'pri_clr': '#ff0000', 
        'sec_clr': '#ff4d4d'
        },
    'gp_prior': {
        'pri_clr': '#ffa500', 
        'sec_clr': '#ffc14d'
    },
    'gp_predict': {
        'pri_clr': '#ff0000', 
        'sec_clr': '#ff4d4d'
    },
    'gp_samps': {
        'clr_cycle': ('#22ffa7', '#f6f926', '#eea6fb', '#c9fbe5', '#00b5f7', 
                      '#e3ee9e', '#fc6955', '#86ce00', '#6e899c', '#0f8508'),
    },

    'unres_len': {
        'pri_clr': '#ff0000', 
        'sec_clr': '#ff4d4d'
    },
    'unres_unlen': {
        'pri_clr': '#ffa500', 
        'sec_clr': '#ffc14d'
    },
    'ps_res_len': {
        'pri_clr': '#fd75ff'
    },
    'bs_res_unlen_pri': {
        'pri_clr': '#5fc0d3', 
        'sec_clr': '#98dbe1'
    },
    'bs_res_unlen_sec': {
        'pri_clr': '#2cce57', 
        'sec_clr': '#73e291'
    },
    'bs_res_len_pri': {
        'pri_clr': '#00e5ff'
    },
    'bs_res_len_sec': {
        'pri_clr': '#0ce4aa'
    },

    'lens': {
        'pri_clr': '#000000', 
        'sec_clr': '#5e5e5e'
    }
}

DEFAULT_PLOT_THEME = DARK_PLOT_THEME


###########################################
# Other Panel Configurations
###########################################
# JS Panel configs
FLOATPANEL_CONFIGS = {
    'headerControls': {'close': 'remove', 'maximize': 'remove'},
    'dragit': {'snap': True},
    'syncMargins': True,
    'resizeit': {'handles':'s'},
    'border': f'{CLRS["page_border"]} solid 0.08rem',
}