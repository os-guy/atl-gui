import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

def create_results_view(window):
    results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
    
    # Başlık
    title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    title_box.set_margin_bottom(16)
    
    title = Gtk.Label(label="Application Results")
    title.add_css_class("title-1")
    title.set_halign(Gtk.Align.CENTER)
    title_box.append(title)
    
    subtitle = Gtk.Label(label="All applications have been run")
    subtitle.add_css_class("subtitle-1")
    subtitle.set_halign(Gtk.Align.CENTER)
    title_box.append(subtitle)
    
    results_box.append(title_box)
    
    # Sonuç listesi için kaydırılabilir alan
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_vexpand(True)
    scrolled_window.set_hexpand(True)
    scrolled_window.set_min_content_height(350)  # Daha makul bir yükseklik
    scrolled_window.set_max_content_height(350)  # Maksimum yükseklik sınırı
    
    # Sonuç listesi
    window.results_list_box = Gtk.ListBox()
    window.results_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
    window.results_list_box.add_css_class("boxed-list")
    scrolled_window.set_child(window.results_list_box)
    
    results_box.append(scrolled_window)
    
    # Özet bilgisi
    window.summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    window.summary_box.set_margin_top(16)
    window.summary_box.set_halign(Gtk.Align.CENTER)
    
    window.summary_label = Gtk.Label()
    window.summary_label.add_css_class("heading")
    window.summary_box.append(window.summary_label)
    
    results_box.append(window.summary_box)
    
    # Butonlar kutusu
    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    button_box.set_margin_top(16)
    button_box.set_halign(Gtk.Align.CENTER)
    
    # Yeni test butonu
    new_test_button = Gtk.Button(label="New Application Test")
    new_test_button.add_css_class("suggested-action")
    new_test_button.add_css_class("pill")
    new_test_button.connect("clicked", window.on_new_test_clicked)
    button_box.append(new_test_button)
    
    # Dışa aktar butonu
    export_button = Gtk.Button(label="Export Results")
    export_button.add_css_class("pill")
    export_button.connect("clicked", window.on_export_clicked)
    button_box.append(export_button)
    
    results_box.append(button_box)
    
    return results_box 