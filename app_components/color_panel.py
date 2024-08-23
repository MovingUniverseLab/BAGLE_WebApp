################################################
# Packages
################################################
import panel as pn
import param
from panel.viewable import Viewer

from app_components import settings_tabs
from app_utils import styles, traces


class ColorPanel(Viewer):
    settings_info = param.ClassSelector(class_ = settings_tabs.SettingsTabs)
    trace_info = param.ClassSelector(class_ = traces.AllTraceInfo)

    # This is a dictionary to label the figure-related color pickers
    FIG_CLR_LABELS = {
        'plot_bg': 'Plot Background',
        'paper_bg': 'Paper Background',
        'ticks': 'Plot Ticks',
        'labels': 'Plot Labels',
        'gridlines': 'Plot Grid Lines',
    }

    def __init__(self, **params):
        self.lock_trigger = False # Boolean to prevetn unwanted updates

        self.theme_dropdown = pn.widgets.Select(
            name = 'Theme',
            sizing_mode = 'stretch_width',
            value = styles.DEFAULT_PLOT_THEME,
            options = {'None': 'None',
                       'Dark': styles.DARK_PLOT_THEME,
                       'Light': styles.LIGHT_PLOT_THEME},
            styles = {'margin-top': '1rem'}
        )

        super().__init__(**params)
        self.pri_clr_label, self.sec_clr_label = self.make_clr_type_labels()

        self.fig_clr_pickers, self.fig_clrs_layout = self.make_fig_clrs_layout()
        self.trace_clr_pickers, self.clr_cycle_tools, self.phot_clr_rows, self.ast_clr_rows, self.phot_clr_layout, self.ast_clr_layout = self.make_trace_clrs_layout()

        self.all_widgets = list(self.fig_clr_pickers.values()) + list(self.clr_cycle_tools.values())
        for trace_key in self.trace_clr_pickers.keys():
            if 'clr_cycle' not in self.trace_clr_pickers[trace_key].keys():
                self.all_widgets += list(self.trace_clr_pickers[trace_key].values())
            else:
                self.all_widgets += self.trace_clr_pickers[trace_key]['clr_cycle']

        self.set_clr_picker_theme()

        self.color_panel_accordion = pn.Accordion(
            toggle = True,
            header_background = styles.CLRS['float_header'],
            active_header_background = styles.CLRS['page_tertiary'],
            sizing_mode = 'stretch_width',
            stylesheets = [styles.ACCORDION_STYLESHEET]
        )

        self.color_panel_note = pn.pane.HTML(
            object = f'''
                <span style="font-size:{styles.FONTSIZES['checkbox_txt']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_secondary']}">
                    <b>Note:</b> This panel can be extended downwards.
                </span>
            ''',
            margin = 0
        )

        self.color_panel_box = pn.FlexBox(
            self.color_panel_note,
            self.color_panel_accordion,
            self.theme_dropdown,
            flex_direction = 'column',
            justify_content = 'center',
            align_items = 'center',
            align_content = 'center',
            sizing_mode = 'stretch_width'
        )

        self.color_floatpanel = pn.layout.FloatPanel(
            self.color_panel_box,
            name = 'Plot Colors',
            contained = False,
            theme = f'{styles.CLRS["float_header"]} fillcolor {styles.CLRS["page_primary"]}',
            height = 300,
            width = 300,
            config = styles.FLOATPANEL_CONFIGS,
            styles = {'overflow':'scroll', 'z-index':'-1'}
        )
        
        # Note: the column is only used here so that we can hide/show the float panel
            # The visible property of the float panel doesn't work when contained = False (used to set page limits on float panel)
        self.color_panel_layout = pn.Column(styles = {'position':'absolute'})

        # Define dependencies
        self.settings_info.genrl_plot_checkbox.param.watch(self.hide_show_floatpanel, 'value')

        for clr_picker in self.fig_clr_pickers.values():
            clr_picker.param.watch(self.clear_theme, 'value', precedence = 10)

        for trace_key in self.trace_clr_pickers.keys():
            if 'clr_cycle' not in self.trace_clr_pickers[trace_key].keys():
                all_clr_pickers = self.trace_clr_pickers[trace_key].values()
            else:
                all_clr_pickers = self.trace_clr_pickers[trace_key]['clr_cycle']

            for clr_picker in all_clr_pickers:
                clr_picker.param.watch(self.clear_theme, 'value', precedence = 10)

    def make_clr_type_labels(self):
        # Note: A color cycle label is currently not needed
        main_clr_types = ['Primary (Time Trace)', 'Secondary (Full Trace)']
        for i, clr_type in enumerate(main_clr_types):
            main_clr_types[i] = pn.pane.HTML(
                    object = f'''
                        <span style="font-size:{styles.FONTSIZES['clr_type_label']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_secondary']}">
                            {clr_type}
                        </span>
                    ''',
                    margin = 0
                )
        return main_clr_types
    
    @pn.depends('theme_dropdown.value', watch = True)
    def set_clr_picker_theme(self):
        theme_dict = self.theme_dropdown.value
        if theme_dict != 'None':
            self.lock_trigger = True

            # Change value of figure color pickers
            for fig_key in self.fig_clr_pickers.keys():
                self.fig_clr_pickers[fig_key].value = theme_dict[fig_key]
            
            # Change value of trace color pickers
            for trace_key in self.trace_clr_pickers.keys():
                if 'clr_cycle' not in theme_dict[trace_key].keys():
                    for clr_key in theme_dict[trace_key].keys():
                        self.trace_clr_pickers[trace_key][clr_key].value = theme_dict[trace_key][clr_key]
                else:
                    for i, clr in enumerate(theme_dict[trace_key]['clr_cycle']):
                        self.trace_clr_pickers[trace_key]['clr_cycle'][i].value = clr

            self.lock_trigger = False

    def make_fig_clrs_layout(self):
        fig_clr_pickers = {}
        fig_clrs_layout = pn.Column(sizing_mode = 'stretch_width', name = 'Figure')

        for key in self.FIG_CLR_LABELS.keys():
            # Make label for color picker row
            key_label = pn.pane.HTML(
                object = f'''
                    <span>{self.FIG_CLR_LABELS[key]}:</span>
                ''',
                styles = {'color': styles.CLRS['txt_primary'],
                          'font-size': styles.FONTSIZES['clr_picker_header'],
                          'font-weight':'bold',
                          'text-align':'center'},
            )

            # Make color picker and set dependency
            fig_clr_pickers[key] = pn.widgets.ColorPicker(
                name = '', 
                styles = styles.COLOR_PICKER_STYLES,
                stylesheets = [styles.COLOR_PICKER_STYLESHEET],
            )

            fig_clrs_layout.extend(
                    [key_label,
                    fig_clr_pickers[key],
                    pn.layout.Divider()]
            )

        return fig_clr_pickers, fig_clrs_layout

    def make_trace_clrs_layout(self):
        phot_clr_rows, ast_clr_rows = {}, {}
        trace_clr_pickers = {} # Dictionary to store all trace color pickers
        clr_cycle_tools = {} # Dictionary to store tools (link switch and opacity slider) for traces that use a color cycle
        for trace_key in self.trace_info.all_traces.keys():
            key_label = pn.pane.HTML(
                object = f'''
                    <span>{self.trace_info.all_traces[trace_key].group_name}:</span>
                ''',
                styles = {'color': styles.CLRS['txt_primary'],
                         'font-size': styles.FONTSIZES['clr_picker_header'],
                         'font-weight':'bold', 
                         'text-align':'center'}
            )
            
            clr_picker_objs = [] # List to store all color picker objects of this trace key (e.g. clr_col)

            if 'clr_cycle' not in styles.DEFAULT_PLOT_THEME[trace_key]:
                clr_picker_dict = {} # Dictionary to better organize primary and secondary color pickers (like in the DARK_PLOT_THEME)
                for clr_type in styles.DEFAULT_PLOT_THEME[trace_key]:
                    if clr_type == 'pri_clr':
                        clr_type_label = self.pri_clr_label
                    else:
                        clr_type_label = self.sec_clr_label

                    # I am using the description property of ColorPicker as an id here.
                        # The caveat of doing this is that we can't set a visible name for the widget, but this isn't too much of an issue. 
                    clr_picker_id = f"('{trace_key}', '{clr_type}')"
                    clr_picker = pn.widgets.ColorPicker(
                        name = '',
                        description = clr_picker_id,
                        sizing_mode = 'stretch_width',
                        margin = 0,
                        styles = {'height': '35px'},
                        stylesheets = [styles.COLOR_PICKER_STYLESHEET]
                    ) 
                    clr_picker_col = pn.FlexBox(
                        clr_type_label,
                        clr_picker, 
                        justify_content = 'center',
                        align_content = 'center',
                        align_items = 'center',
                        styles = {
                            'width': '46%',
                            'height':'fit-content',
                            'margin-left':'2%',
                            'margin-right':'2%'
                        }
                    )
                    clr_picker_objs.append(clr_picker_col)
                    clr_picker_dict[clr_type] = clr_picker

                trace_clr_row_content = [key_label]
                trace_clr_pickers[trace_key] = clr_picker_dict
        
            else:
                # Make color pickers for each color in color cycle
                for i in range(len(styles.DEFAULT_PLOT_THEME[trace_key]['clr_cycle'])):
                    clr_picker_id = f"('{trace_key}', 'clr_cycle', {i})"
                    clr_picker = pn.widgets.ColorPicker(
                        name = '',
                        description = clr_picker_id,
                        styles = styles.COLOR_PICKER_STYLES,
                        stylesheets = [styles.COLOR_PICKER_STYLESHEET]
                    ) 
                    clr_picker_objs.append(clr_picker)

                clr_cycle_note = pn.pane.HTML(
                    object = f'''
                        <span style="font-size:{styles.FONTSIZES['checkbox_txt']};font-family:{styles.HTML_FONTFAMILY};color:{styles.CLRS['txt_secondary']}">
                            <b>Note:</b> These color pickers are for the color cycle used for the sample traces.
                        </span>
                    '''
                )

                # Make switch to link color pickers specifically for this trace key
                clr_cycle_tools[trace_key, 'link_switch'] = pn.widgets.Switch(
                    name = '', 
                    align = 'start', 
                    stylesheets = [styles.SWITCH_STYLESHEET],
                    styles = {'margin-right':'0'}
                )

                switch_label = pn.pane.HTML(
                    object = f'''
                        <span>Link Color Pickers</span>
                    ''',
                    styles = {'color': styles.CLRS['txt_primary'],
                             'font-size': styles.FONTSIZES['checkbox_txt'],
                             'text-align':'center'},
                )

                switch_row = pn.Row(clr_cycle_tools[trace_key, 'link_switch'], switch_label, styles = {'margin-bottom': '0.2rem'})
                trace_clr_row_content = [key_label, clr_cycle_note, switch_row]
                trace_clr_pickers[trace_key] = {'clr_cycle': clr_picker_objs}

            clr_picker_box = pn.FlexBox(
                objects = clr_picker_objs,
                sizing_mode = 'stretch_width',
                flex_direction = 'row',
                justify_content = 'space-between'
            )
                
            trace_clr_row_content.extend([clr_picker_box, pn.layout.Divider(margin = 0)])

            trace_clr_row = pn.Column(objects = trace_clr_row_content)

            if trace_key in self.trace_info.phot_traces.keys():
                phot_clr_rows[trace_key] = trace_clr_row
            elif trace_key in self.trace_info.ast_traces.keys():
                ast_clr_rows[trace_key] = trace_clr_row

        phot_clrs_layout = pn.Column(objects = list(phot_clr_rows.values()), name = 'Photometry Traces')
        ast_clrs_layout = pn.Column(objects = list(ast_clr_rows.values()), name = 'Astrometry Traces')

        return trace_clr_pickers, clr_cycle_tools, phot_clr_rows, ast_clr_rows, phot_clrs_layout, ast_clrs_layout

    @pn.depends('settings_info.errored_state', watch = True)
    def set_errored_layout(self):
        if self.settings_info.errored_state == False:
            for widget in self.all_widgets:
                widget.disabled = False
        else:
            for widget in self.all_widgets:
                widget.disabled = True

    def clear_theme(self, *event):
        '''
        This is a function to change theme button to None whenever a color picker is used
        '''
        if self.lock_trigger == False:
            self.theme_dropdown.value = 'None'

    @pn.depends('settings_info.genrl_plot_checkbox.value',
                'settings_info.phot_checkbox.value', 'settings_info.ast_checkbox.value', watch = True)
    def hide_show_clr_pickers(self):
        if (self.settings_info.lock_trigger == False) and ('color' in self.settings_info.genrl_plot_checkbox.value):
            # Disable secondary color picker if no full traces
            full_trace_bool = 'full_trace' in self.settings_info.genrl_plot_checkbox.value
            for trace_key in self.trace_clr_pickers.keys():
                if 'sec_clr' in styles.DEFAULT_PLOT_THEME[trace_key].keys():
                    self.trace_clr_pickers[trace_key]['sec_clr'].disabled = not full_trace_bool

            # Hide/show photometry color pickers
            for trace_key in self.phot_clr_rows.keys():
                if trace_key in self.trace_info.main_phot_keys + self.trace_info.extra_phot_keys:
                    self.phot_clr_rows[trace_key].visible = True
                else:
                    self.phot_clr_rows[trace_key].visible = False
            
            # Hide/show astrometry color pickers
            for trace_key in self.ast_clr_rows.keys():
                if trace_key in self.trace_info.main_ast_keys + self.trace_info.extra_ast_keys:
                    self.ast_clr_rows[trace_key].visible = True
                else:
                    self.ast_clr_rows[trace_key].visible = False

    @pn.depends('settings_info.dashboard_checkbox.value', watch = True)
    def hide_show_cards(self):
        if (self.settings_info.lock_trigger == False) and ('color' in self.settings_info.genrl_plot_checkbox.value):
            content_cards = [self.fig_clrs_layout]
            if len(self.trace_info.selected_phot_plots) != 0:
                content_cards.append(self.phot_clr_layout)
            if len(self.trace_info.selected_ast_plots) != 0:
                content_cards.append(self.ast_clr_layout)

            self.color_panel_accordion.objects = content_cards
            # This will close all cards in the accordion
            self.color_panel_accordion.active = []

    def hide_show_floatpanel(self, *event):
        match ['color' in event[0].old, 'color' in event[0].new]:
            case [False, True]:
                self.hide_show_cards()
                self.hide_show_clr_pickers()
                self.color_panel_layout.objects = [self.color_floatpanel]

            case [_, False]:
                self.color_panel_layout.clear()

    def __panel__(self):
        return self.color_panel_layout