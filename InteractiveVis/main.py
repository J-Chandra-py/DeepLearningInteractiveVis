#!/usr/bin/env python
# coding: utf-8
# controller module

from config import debug
from config import translations
from datamodel import index_lst, sorted_xs, Model
import view
from bokeh.events import Tap, Pan, MouseWheel
from bokeh.models.callbacks import CustomJS
import numpy as np
import time

def select_language_callback(attr, old_value, new_value):
    """
    Called if user has selected a new language.
    """
    if debug: print("Called select_language_callback().")
    # keep track of current sex
    sex_index = v.lexicon["sex_catg"].index(v.sex_select.value)
    v.lexicon = translations[new_value]
    v.curdoc().hold()
    
    v.lang_title_div.update(text=v.lexicon["lang"])
    v.subject_select.update(title=v.lexicon["subject"])
    v.model_select.update(title=v.lexicon["model"])
    v.threshold_slider.update(title=v.lexicon["relv_th"])
    v.clusthist.title.text=v.lexicon["clusthist_title"]
    v.clustersize_slider.update(title=v.lexicon["min_cluster"])
    v.transparency_slider.update(title=v.lexicon["transparency"])
    v.toggle_transparency.update(label=v.lexicon["t_transparency"])
    v.toggle_regions.update(label=v.lexicon["t_regions"])
    v.region_div.update(text=v.lexicon["region"])
    v.cluster_size_div.update(text=v.lexicon["cluster_size"])
    v.cluster_mean_div.update(text=v.lexicon["mean"])
    v.cluster_peak_div.update(text=v.lexicon["peak"])
    v.age_spinner.update(title=v.lexicon["age"])
    v.sex_select.update(title=v.lexicon["sex"])
    v.sex_select.update(options=v.lexicon["sex_catg"], value=v.lexicon["sex_catg"][sex_index])
    v.tiv_spinner.update(title=v.lexicon["tiv"])
    v.field_strength_select.update(title=v.lexicon["field_strength"])
    v.file_uploaded_lbl.update(text=v.lexicon["upload_status1"])
    v.prepare_button.update(label=v.lexicon["prepare_label"])
    v.slice_slider_frontal.update(title=v.lexicon["c_slice"])
    v.guide_frontal.title.text=v.lexicon["relv_plot_title"]
    v.flip_frontal_view.update(label=v.lexicon["t_frontal_view"])
    v.processing_label.update(text=v.lexicon["processing_label"])
    v.scan_upload_label.update(text=v.lexicon["upload_label"])
    v.slice_slider_axial.update(title=v.lexicon["a_slice"])
    v.guide_axial.title.text=v.lexicon["relv_plot_title"]
    v.slice_slider_sagittal.update(title=v.lexicon["s_slice"])
    v.guide_sagittal.title.text=v.lexicon["relv_plot_title"]
    v.color_bar.update(title=v.lexicon["relv_scale_title"])
    v.p_color_bar.add_layout(v.color_bar)
    if m.pred is None:
        v.prediction_label.update(text = v.lexicon["scan_evaluate"])
    elif int(m.pred) == 0 and not v.processing_done:
        v.prediction_label.update(text = v.lexicon["enter_and_process"])
    else:
        v.prediction_label.update(text = v.lexicon["likelihood"] % m.pred)
    v.color_mode.update(label=v.lexicon["theme_label"])

    v.curdoc().add_root(v.layout)
    v.curdoc().unhold()
    

def click_frontal_callback(event):
    """
    Called if user has clicked or dragged the mouse on frontal plot.

    Normalizes the coordinates in the given event and sets the sagittal and axial sliders accordingly, which
    will redraw plots and update cross hair positions.
    :param event: click event with x and y coordinates
    :return: None
    """
    if debug: print("Called click_frontal_callback().")
    global dontplot  # helper variable to not plot the same image twice

    # normalising click coordinates
    if event.x < 1:
        x = 1
    elif event.x > v.slice_slider_sagittal.end:
        x = v.slice_slider_sagittal.end
    else:
        x = int(round(event.x))

    if event.y < 1:
        y = 1
    elif event.y > v.slice_slider_axial.end:
        y = v.slice_slider_axial.end
    else:
        y = int(round(event.y))

    dontplot = True
    v.slice_slider_sagittal.update(value=x)
    dontplot = False
    v.slice_slider_axial.update(value=y)
    if not v.toggle_regions.active: v.plot_sagittal()


def click_axial_callback(event):
    """
    Called if user has clicked or dragged the mouse on axial plot.

    Normalizes the coordinates in the given event and sets the frontal and sagittal sliders accordingly, which
    will redraw plots and update cross hair positions.
    :param event: click event with x and y coordinates
    :return: None
    """
    if debug: print("Called click_axial_callback().")
    global dontplot

    # normalising click coordinates
    if event.x < 1:
        x = 1
    elif event.x > v.slice_slider_sagittal.end:
        x = v.slice_slider_sagittal.end
    else:
        x = int(round(event.x))

    if event.y < 1:
        y = 1
    elif event.y > v.slice_slider_frontal.end:
        y = v.slice_slider_frontal.end
    else:
        y = int(round(event.y))

    dontplot = True
    v.slice_slider_frontal.update(value=v.slice_slider_frontal.end - y + 1)
    dontplot = False
    v.slice_slider_sagittal.update(value=x)
    if not v.toggle_regions.active: v.plot_frontal()


def click_sagittal_callback(event):
    """
    Called if user has clicked or dragged the mouse on sagittal plot.

    Normalizes the coordinates in the given event and sets the frontal and axial sliders accordingly, which
    will redraw plots and update cross hair positions.
    :param event: click event with x and y coordinates
    :return: None
    """
    if debug: print("Called click_sagittal_callback().")
    global dontplot

    # normalising click coordinates
    if event.x < 1:
        x = 1
    elif event.x > v.slice_slider_frontal.end:
        x = v.slice_slider_frontal.end
    else:
        x = int(round(event.x))

    if event.y < 1:
        y = 1
    elif event.y > v.slice_slider_axial.end:
        y = v.slice_slider_axial.end
    else:
        y = int(round(event.y))

    dontplot = True
    v.slice_slider_frontal.update(value=x)
    dontplot = False
    v.slice_slider_axial.update(value=y)
    if not v.toggle_regions.active: v.plot_frontal()


def select_subject_worker():
    """
    Handles the final layout of the Bokeh layout.

    Sets the subject image and background based on the selected subject type (internal or user-uploaded),
    updates the covariate GUI elements, and redraws the coronal, axial, and sagittal plots for the currently
    selected scan. Concludes by enabling the widgets.

    :return: None
    """
    if debug: print("Called select_subject_worker().")
    v.curdoc().hold()
    # if not v.firstrun:  # Avoid duplicate set_subject() call when application first starts. # redundant
    if (v.subject_select.value != "User Upload"):
        if debug: print("Using internal scan.....")
        m.set_subject(index_lst[sorted_xs.index(v.subject_select.value)])  # this parameter is subj_id
        v.update_covariate_info(index_lst[sorted_xs.index(
            v.subject_select.value)], None)  # called with subj_id; corresponding RID/sid would be m.grps.iloc[m.index_lst[m.sorted_xs.index(v.subject_select.value)], 1]
        v.freeze_covariates()
    else:
        if debug: print("Using uploaded scan.....")
        m.set_subj_img(m.uploaded_residual)
        m.set_subj_bg(m.uploaded_bg_img)
        v.update_covariate_info(None, m.entered_covariates_df)
        v.make_covariates_editable()
    # if m.pred is None:
    #     v.prediction_label.text = v.lexicon["scan_evaluate"]
    # else:
    v.prediction_label.text = v.lexicon["likelihood"] % m.pred
    v.p_frontal.title.text=" "
    v.p_axial.title.text = " "
    v.p_sagittal.title.text = " "
    v.render_backround()
    v.apply_thresholds(m.relevance_map, threshold=v.threshold_slider.value, cluster_size=v.clustersize_slider.value)
    v.update_cluster_sizes_histogram()
    v.update_guide_frontal()
    v.update_guide_axial()
    v.update_guide_sagittal()
    v.plot_frontal()
    v.plot_axial()
    v.plot_sagittal()
    v.update_cluster_divs()
    v.enable_widgets()
    v.update_processing_label(make_visible=False)
    v.curdoc().unhold()

def select_subject_callback(attr, old, new):
    """
    Called if new subject has been selected.

    Disables the widgets for user input and calls the worker method for selecting a new subject (which will e.g. re-plot
    the figures etc.).

    :param attr: not used
    :param str old: the old value, not used
    :param str new: the new value of the subject selected (i.e. the name), not used
    :return: None
    """
    if debug: print("Called select_subject_callback().")

    # Ensure subject_worker is not triggered before bg and residual data are calculated.
    # This avoids initializing with empty data, which can lead to incorrect label behavior.
    if v.subject_select.value == "User Upload" and not v.processing_done:
        if debug: print("processing not done, skipping the select_subject_callback")
        pass
    else:
        v.update_processing_label(make_visible=True)
        v.prediction_label.text = v.lexicon["scan_evaluate"]
        v.disable_widgets()
        v.freeze_covariates()
        v.curdoc().add_next_tick_callback(select_subject_worker)

def select_model_worker():
    """
    Sets the new selected model and calls "select_subject_worker".

    :return: None
    """
    if debug: print("Called select_model_worker().")

    # Might take a long time if model is not cached yet.
    m.set_model(v.model_select.value)
    print("Finished selecting new model.")
    v.curdoc().add_next_tick_callback(select_subject_worker)


def select_model_callback(attr, old, new):
    """
    Only disables widgets for user interaction and calls select_model_worker-method.

    :param attr: not used
    :param old: previously selected model, not used
    :param new: the new selected model name ("newmodel/newmodel_cb_....") in the model selection box, not used
    :return: None
    """
    if debug: print("Called select_model_callback().")

    v.update_processing_label(make_visible=True)
    v.prediction_label.text = v.lexicon["scan_evaluate"]
    v.disable_widgets()
    v.curdoc().add_next_tick_callback(select_model_worker)


def apply_thresholds_callback(attr, old, new):
    """
    Called if threshold_slider or clustersize_slider value been modified.
    Re-plots the figures and guides with updated overlay.

    :param attr: not used
    :param old: not used
    :param new: not used
    :return: None
    """
    if debug: print("Called apply_thresholds_callback().")

    v.apply_thresholds(m.relevance_map, threshold=v.threshold_slider.value, cluster_size=v.clustersize_slider.value)
    v.update_cluster_sizes_histogram()
    v.update_guide_frontal()
    v.update_guide_axial()
    v.update_guide_sagittal()
    v.update_cluster_divs()
    v.plot_frontal()
    v.plot_axial()
    v.plot_sagittal()


def set_slice_frontal_mouse_wheel(event):
    """
    Called when mouse wheel is used on the frontal slice view.
    
    :param MouseWheel event: float delta contains the (signed) scroll speed.
    :return: None
    """
    if event.delta > 0 and v.slice_slider_frontal.value > v.slice_slider_frontal.start:
        v.slice_slider_frontal.value -= 1
    elif event.delta < 0 and v.slice_slider_frontal.value < v.slice_slider_frontal.end:
        v.slice_slider_frontal.value += 1
    print("Mouse Scroll Event Fired on Frontal")

def set_slice_axial_mouse_wheel(event):
    """
    Called when mouse wheel is used on the axial slice view.
    
    :param MouseWheel event: float delta contains the (signed) scroll speed.
    :return: None
    """
    if event.delta > 0 and v.slice_slider_axial.value < v.slice_slider_axial.end:
        v.slice_slider_axial.value += 1 
    elif event.delta < 0 and v.slice_slider_axial.value > v.slice_slider_axial.start:
        v.slice_slider_axial.value -= 1 
    print("Mouse Scroll Event Fired on Axial")

def set_slice_sagittal_mouse_wheel(event):
    """
    Called when mouse wheel is used on the sagittal slice view.
    
    :param MouseWheel event: float delta contains the (signed) scroll speed.
    :return: None
    """
    if event.delta > 0 and v.slice_slider_sagittal.value < v.slice_slider_sagittal.end:
        v.slice_slider_sagittal.value += 1 
    elif event.delta < 0 and v.slice_slider_sagittal.value > v.slice_slider_sagittal.start:
        v.slice_slider_sagittal.value -= 1 
    print("Mouse Scroll Event Fired on Sagittal")
 

def set_slice_frontal_callback(attr, old, new):
    """
    Called if the slice_slider_frontal has been modified (directly by user or or indirectly via click event)

    Usually re-plots the frontal figure (and the others if region outline is active). Also relocates the cross hairs
    indicating the selected frontal slice.

    :param attr: not used
    :param old: not used
    :param int new: the frontal slider value
    :return: None
    """
    if debug: print("Called set_slice_frontal_callback().")

    v.axial_crosshair_from_frontal.update(location=v.slice_slider_frontal.end - new + 1)
    v.sagittal_crosshair_from_frontal.update(location=new)
    v.update_region_div()
    v.update_cluster_divs()
    if not dontplot:  # is set True if called from click_*_callback()
        v.plot_frontal()
    if v.toggle_regions.active and not dontplot:
        v.plot_axial()
        v.plot_sagittal()


def set_slice_axial_callback(attr, old, new):
    """
    Called if the slice_slider_axial has been modified (directly by user or or indirectly via click event)

    Usually re-plots the axial figure (and the others if region outline is active). Also relocates the cross hairs
    indicating the selected axial slice.

    :param attr: not used
    :param old: not used
    :param int new: the axial slider value
    :return: None
    """
    if debug: print("Called set_slice_axial_callback().")

    v.frontal_crosshair_from_axial.update(location=new)
    v.sagittal_crosshair_from_axial.update(location=new)
    v.update_region_div()
    v.update_cluster_divs()
    if not dontplot:
        v.plot_axial()
    if v.toggle_regions.active and not dontplot:
        v.plot_frontal()
        v.plot_sagittal()


def set_slice_sagittal_callback(attr, old, new):
    """
    Called if the slice_slider_sagittal has been modified (directly by user or or indirectly via click event)

    Usually re-plots the sagittal figure (and the others if region outline is active). Also relocates the cross hairs
    indicating the selected sagittal slice.

    :param attr: not used
    :param old: not used
    :param int new: the sagittal slider value
    :return: None
    """
    if debug: print("Called set_slice_sagittal_callback().")

    v.frontal_crosshair_from_sagittal.update(location=new)
    v.axial_crosshair_from_sagittal.update(location=new)
    v.update_region_div()
    v.update_cluster_divs()
    if not dontplot:
        v.plot_sagittal()
    if v.toggle_regions.active and not dontplot:
        v.plot_frontal()
        v.plot_axial()


def set_transparency_callback(attr, old, new):
    """
    Called if the transparency_slider has been modified by the user.

    Re-plots the figures with updated overlay (with selected transparency).

    :param attr: not used
    :param old: not used
    :param new: not used
    :return: None
    """
    if debug: print("Called set_transparency_callback().")
    v.render_overlay()
    v.plot_frontal()
    v.plot_axial()
    v.plot_sagittal()


# This list will save the old value of transparency_slider
old_transparency = []
def click_transparency_change(attr):
    """
        This function controls the transparency of the overlay on
        "hide overlay" button click.
    
    """
    if debug: print("Called click_transperency_change().")
    if v.toggle_transparency.active:
        old_transparency.clear()
        old_transparency.append(v.transparency_slider.value)
        v.transparency_slider.value = 1
    else:
        v.transparency_slider.value = old_transparency[0]


def click_show_regions_callback(attr):
    """
    Called if the "Show region outline" button has been pressed.

    Re-plots all figures.

    :param attr:  not used
    :return: None
    """
    if debug: print("Called click_show_regions_callback().")
    v.plot_frontal()
    v.plot_axial()
    v.plot_sagittal()


def flip_frontal_callback(attr):
    """
    Called if "Flip L/R orientation" button has been pressed.

    Updates the orientation labels, figures and sliders with the mirrored versions.

    :param attr: not used
    :return: None
    """
    if debug: print("Called flip_frontal_callback().")
    v.orientation_label_shown_left.update(text="R" if v.flip_frontal_view.active else "L")
    v.orientation_label_shown_right.update(text="L" if v.flip_frontal_view.active else "R")
    v.update_region_div()
    v.slice_slider_sagittal.update(value=np.abs(v.slice_slider_sagittal.end - v.slice_slider_sagittal.value) + 1)
    v.plot_frontal()
    v.plot_axial()
    v.update_guide_sagittal()

def reset_scan_overlay():
    """
    Resets the scan overlay settings for the uploaded scan process.

    Activates user interface widgets and updates the subject selection to include "User Upload", defaulting to it. 
    Temporarily disables model and subject selection to limit interaction until the uploaded scan is evaluated.
    Updates the visibility of UI labels related to file uploads and scan processing status.

    :return: None
    """
    if debug: print("Called reset_scan_overlay().")
    # time.sleep(5) # redundant, using next_tick
    v.enable_widgets()
    v.subject_select.update(options=(["User Upload"]+sorted_xs), value="User Upload") # Uploaded scan reference is added to "Subjects:""list
    # Limit user control until the uploaded scan is evaluated. (*)
    v.model_select.update(disabled=True)
    v.subject_select.update(disabled=True)      
    v.file_uploaded_lbl.update(visible=True)
    v.update_scan_label(make_visible=False)

def change_visualization_to_empty_overlay():
    """
    Sets an overlay with empty residuals to the coronal, axial, and sagittal plots for the currently
    uploaded scan.

    :return: None
    """
    if debug: print("Called change_visualization_to_empty_overlay()")
    m.reset_prepared_data(m.uploaded_bg_img) # set empty residuals
    m.set_subj_img(m.uploaded_residual)
    m.set_subj_bg(m.uploaded_bg_img)
    v.prediction_label.text = v.lexicon["enter_and_process"]
    v.render_backround()
    v.apply_thresholds(m.relevance_map, threshold=v.threshold_slider.value, cluster_size=v.clustersize_slider.value)
    v.update_cluster_sizes_histogram()
    v.update_guide_frontal()
    v.update_guide_axial()
    v.update_guide_sagittal()
    v.plot_frontal()
    v.plot_axial()
    v.plot_sagittal()
    v.update_cluster_divs()
    v.make_covariates_editable()
    v.curdoc().add_next_tick_callback(reset_scan_overlay)

def upload_scan_callback(attr, old, new):
    """
    Called if a new file has been uploaded.
    Attempts to load the file as array and enable covariate widgets for entering values
    for processing.
    Also sets initial values for the covariates.

    :param attr: not used
    :param old: not used
    :param new: the uploaded file encoded as base64 string
    :return: None
    """
    if debug: print("Called upload_scan_callback()")

    is_zipped = v.scan_upload.filename.endswith('.gz')
    # Set initial average values:
    v.age_spinner.update(value=73)
    v.sex_select.update(value=v.lexicon["sex_catg"][2])
    v.tiv_spinner.update(value=1400)
    v.field_strength_select.update(value='3.0')
    # disabling processing flag for every user upload
    v.processing_done = False
    try:
        #Pops up "Uploading scan..." overlay
        v.update_scan_label(make_visible=True)
        v.disable_widgets()
        v.freeze_covariates()
        m.load_nifti(new, is_zipped)
        v.curdoc().add_next_tick_callback(change_visualization_to_empty_overlay)
    except Exception as e:
        v.prediction_label.text = str(type(e).__name__)+": "+str(e)
        print("Exception: {}".format(type(e).__name__))
        print("Exception message: {}".format(e))

def prepare_data_worker():
    """
    This exists just to pack all heavy work for processing in one callback method for bokeh's add_next_tick_callback(...)

    :return: None
    """
    print("Called prepare_data_worker()")
    # prepare the data for CNN model input, which might take a while:
    m.prepare_data(m.uploaded_bg_img)
    v.processing_done = True # enabling processing flag
    # update the visualization:
    v.curdoc().add_next_tick_callback(select_subject_worker)
    # v.enable_widgets() # redundant; because subject_worker already does it

def enter_covariates_callback():
    """
    Called if the 'Start processing and evaluate scan' button has been pressed for own data uploaded by the user.
    Disables widgets, shows 'loading label' and performs processing work.

    :return: None
    """
    if debug: print("Called enter_covariates_callback")
    m.pred = None  # revert the prev prediction
    v.update_processing_label(make_visible=True)
    v.file_uploaded_lbl.update(visible=False)
    v.prediction_label.text = v.lexicon["scan_evaluate"]
    v.disable_widgets()
    v.freeze_covariates()
    sex_identifier = 0.5
    if (v.sex_select.value == v.lexicon["sex_catg"][1]):
        sex_identifier = 1.0
    elif (v.sex_select.value == v.lexicon["sex_catg"][0]):
        sex_identifier = 0.0
    m.set_covariates(v.age_spinner.value, sex_identifier, v.tiv_spinner.value, float(v.field_strength_select.value))
    v.curdoc().add_next_tick_callback(prepare_data_worker) # early return, do the heavy work on next tick


dontplot = False
m = Model()  # construct new datamodel object for storing selected subject/cnn model per session
# construct new View object for every session since bokeh models (i.e. sliders, figures, ...)
# cannot be shared across client sessions:
v = view.View(m)

# JavaScript callback for switching theme based on 'data' value of current_theme data element
switch_theme_callback = CustomJS(args=dict(source=v.current_theme), code="""
    var data = source.data;
    var currentTheme = data['theme'][0];
    var newTheme;

    // Toggle theme
    if (currentTheme === 'light') {
        newTheme = 'dark';
    } else {
        newTheme = 'light';
    }

    // Update the theme
    data['theme'][0] = newTheme;
    source.change.emit(); // Emit change to notify Bokeh
    var sliderActiveRanges = document.querySelectorAll('.noUi-connect');
    
    // Apply theme to the body
    if (newTheme === 'dark') {
        document.body.classList.add('dark-mode');
        // console.log("Adding dark mode: true");
        sliderActiveRanges.forEach(function(range) {
                range.style.backgroundColor =  "#333333"; // Dark gray for active area
            });
    } else {
        document.body.classList.remove('dark-mode');
        // console.log("Adding dark mode: false");
        sliderActiveRanges.forEach(function(range) {
                range.style.backgroundColor =  "#E6E6E6"; // Light gray for active area
            });
    }
""")

# handle clicking events
v.p_frontal.on_event(Tap, click_frontal_callback)
v.p_frontal.on_event(Pan, click_frontal_callback)
v.p_axial.on_event(Tap, click_axial_callback)
v.p_axial.on_event(Pan, click_axial_callback)
v.p_sagittal.on_event(Tap, click_sagittal_callback)
v.p_sagittal.on_event(Pan, click_sagittal_callback)
# handle Mouse Wheel events
v.p_frontal.on_event(MouseWheel, set_slice_frontal_mouse_wheel)
v.p_axial.on_event(MouseWheel, set_slice_axial_mouse_wheel)
v.p_sagittal.on_event(MouseWheel, set_slice_sagittal_mouse_wheel)

# for jupyter notebook:
# show(layout)
# alternatively, add layout to the document (for bokeh server)
v.curdoc().add_root(v.layout)
v.curdoc().title = 'Online AD brain viewer'

# Set callbacks for events:
v.subject_select.on_change('value', select_subject_callback)
v.model_select.on_change('value', select_model_callback)
v.prepare_button.on_click(enter_covariates_callback)
v.scan_upload.on_change("value", upload_scan_callback)

# callback for language
v.lang_select.on_change("value", select_language_callback)

# callback for background
v.color_mode.js_on_click(switch_theme_callback)

v.curdoc().hold()
# select_subject_callback('', '', '') # redundant, instead directly calling select_subject_worker
if debug: print(f"Flag check firstrun: {v.firstrun}")
if v.firstrun: select_subject_worker() # call once at the application start with a preselected internal scan (AD ID - 4001)
# v.curdoc().unhold() #Redundant, is already unhold in select_subject_worker() call.
v.firstrun = False

# Set callbacks for plot control events
v.slice_slider_frontal.on_change('value', set_slice_frontal_callback)
v.slice_slider_axial.on_change('value', set_slice_axial_callback)
v.slice_slider_sagittal.on_change('value', set_slice_sagittal_callback)
v.flip_frontal_view.on_click(flip_frontal_callback)
v.threshold_slider.on_change('value', apply_thresholds_callback)
v.clustersize_slider.on_change('value', apply_thresholds_callback)
v.transparency_slider.on_change('value', set_transparency_callback)
v.toggle_transparency.on_click(click_transparency_change)
v.toggle_regions.on_click(click_show_regions_callback)

# automatically close bokeh after browser window was closed
# def close_session(session_context):
#    sys.exit()  # Stop the server
# v.curdoc().on_session_destroyed(close_session)