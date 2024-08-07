################################################
# Packages
################################################
import panel as pn


################################################
# Dashboard - Indicators
################################################
loading = pn.pane.GIF('./custom_indicators/loading_indicator/loading_indicator.gif', name = 'loading_indicator', width = 150)
error = pn.pane.GIF('./custom_indicators/error_indicator/error_indicator.gif', name = 'error_indicator', width = 180)