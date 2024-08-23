################################################
# Packages
################################################
import panel as pn


################################################
# Dashboard - Indicators
################################################
startup= pn.pane.GIF('./custom_indicators/startup_indicator/startup_indicator.gif', name = 'startup_indicator', width = 200, margin = (50, 0, 0, 0))
component_loading = pn.pane.GIF('./custom_indicators/component_loading_indicator/component_loading_indicator.gif', name = 'component_loading_indicator', width = 150)
error = pn.pane.GIF('./custom_indicators/error_indicator/error_indicator.gif', name = 'error_indicator', width = 180)