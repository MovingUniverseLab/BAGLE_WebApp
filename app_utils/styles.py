
################################################
# Packages
################################################
import panel as pn


###########################################
# Colors and Themes
###########################################
THEMES = {
    'page_theme': 'dark',
    'page_design': 'bootstrap',
    'slider_design': pn.theme.Material,
    'code_theme': 'tomorrow_night_eighties',
}

# The colors chosen match the dark theme of Panel
CLRS = {
    'page_primary': 'rgb(18, 18, 18)',
    'page_secondary': 'rgb(43, 48, 53)',
    'page_light': 'rgb(75, 255, 239)',
    'page_selected': 'rgb(101, 175, 233)',
    'page_border': 'rgb(255, 255, 255)',
    'txt_primary': 'rgb(255, 255, 255)',
    'txt_secondary': 'rgb(204, 204, 204)',
    'error_primary': 'rgb(255, 0, 0)',
    'error_secondary': 'rgb(179, 0, 89)',
    'summary_vector': 'rgb(153, 153, 153)',
    'plot_gridline': 'rgb(102, 102, 102)',
}

# This is for the color cycle of the GP samples
GP_ALPHA = 0.7
GP_SAMP_CLRS = (
    f'rgba(34, 255, 167, {GP_ALPHA})',
    f'rgba(246, 249, 38, {GP_ALPHA})',
    f'rgba(238, 166, 251, {GP_ALPHA})',
    f'rgba(201, 251, 229, {GP_ALPHA})',
    f'rgba(0, 181, 247, {GP_ALPHA})',
    f'rgba(227, 238, 158, {GP_ALPHA})',
    f'rgba(252, 105, 85, {GP_ALPHA})',
    f'rgba(134, 206, 0, {GP_ALPHA})',
    f'rgba(110, 137, 156, {GP_ALPHA})',
    f'rgba(15, 133, 84, {GP_ALPHA})'
)

###########################################
# Fonts
###########################################
HTML_FONTFAMILY = 'Helvetica'

# Dictionary for font sizes
FONTSIZES = {
    'page_title':' 1.6rem',
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
    'plot_legendgroup': 9
}

###########################################
# CSS Styles and Stylesheets
###########################################
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

################################################
# Photometry and Astrometry Plot Formats
################################################
PLOT_WIDTH = 49.75 # plot width in percentage

BASE_PLOTBOX_STYLES = {
    'background': CLRS['page_secondary'],
    'border': f'{CLRS["page_border"]} solid 0.08rem', 
    'height': '100%',
    'width': f'{PLOT_WIDTH}%',
    'flex-shrink': '0'
}

EXPANDED_PLOTBOX_STYLES = {
    'background': CLRS['page_secondary'],
    'border': f'{CLRS["page_border"]} solid 0.08rem', 
    'height': '100%',
    'width': '100%',
    'flex-shrink': '0'
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

PHOT_PLOT_NAMES = ['phot']
AST_PLOT_NAMES = ['ast_radec', 'ast_ra', 'ast_dec']
FORMAT_DICT = {
    'phot': (PHOT_TITLE, PHOT_XY),
    'ast_radec': (RADEC_TITLE, RADEC_XY),
    'ast_ra': (RA_TITLE, RA_XY),
    'ast_dec': (DEC_TITLE, DEC_XY)
}