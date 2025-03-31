import gi
import os
import datetime
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango

def show_test_results(self):
    # Görünümleri değiştir
    self.welcome_view.set_visible(False)
    self.testing_view.set_visible(False)
    self.results_view.set_visible(True)
    
    # Önceki sonuçları temizle - GTK4 uyumlu şekilde
    while True:
        row = self.results_list_box.get_first_child()
        if row is None:
            break
        self.results_list_box.remove(row)
    
    # Özet için sayaçlar
    working_count = 0
    not_working_count = 0
    skipped_count = 0
    
    # Her APK için sonuçları ekle
    for apk_path, result in self.test_results.items():
        apk_name = os.path.basename(apk_path)
        
        # Expandable row için bir container oluştur
        expander = Adw.ExpanderRow()
        expander.set_title(apk_name)
        
        # İkon ekle
        if result == "working":
            icon = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
            icon.add_css_class("success")
            expander.add_prefix(icon)
            expander.add_css_class("success")
            expander.set_subtitle("Working")
            working_count += 1
        elif result == "not_working":
            icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
            icon.add_css_class("error")
            expander.add_prefix(icon)
            expander.add_css_class("error")
            expander.set_subtitle("Not Working")
            not_working_count += 1
        else:  # skipped
            icon = Gtk.Image.new_from_icon_name("action-unavailable-symbolic")
            expander.add_prefix(icon)
            expander.add_css_class("dim-label")
            expander.set_subtitle("Skipped")
            skipped_count += 1
            
        # Terminal loglarını ekle - terminal_logs olup olmadığını kontrol et
        if hasattr(self, 'terminal_logs') and apk_path in self.terminal_logs:
            # Terminal logu varsa, bir metin görünümü içinde göster
            log_view = Gtk.TextView()
            log_view.set_editable(False)
            log_view.set_cursor_visible(False)
            log_view.add_css_class("log-view")
            log_view.get_buffer().set_text(self.terminal_logs[apk_path])
            
            # Loglar için CSS - ince border
            css_provider = Gtk.CssProvider()
            css_data = """
                textview.log-view {
                    background-color: #f8f8f8;
                    color: #202020;
                    padding: 4px;
                    border-radius: 3px;
                    font-family: monospace;
                    font-size: 12px;
                    margin: 4px;
                    border: 0.25px solid #e8e8e8;
                }
                textview.log-view text {
                    background-color: #f8f8f8;
                    color: #202020;
                }
            """
            css_provider.load_from_data(css_data.encode('utf-8'))
            style_context = log_view.get_style_context()
            style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            
            # Kaydırılabilir alan içine yerleştir
            log_scroll = Gtk.ScrolledWindow()
            log_scroll.set_min_content_height(150)
            log_scroll.set_vexpand(True)
            log_scroll.set_child(log_view)
            
            # İlk önce row'a prefixleri ekle, sonra log_box'ı
            log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            log_box.set_margin_start(8)
            log_box.set_margin_end(8)
            log_box.set_margin_bottom(8)
            log_box.append(log_scroll)
            
            # İlk önce row'a prefixleri ekle, sonra log_box'ı
            expander.add_row(log_box)
        else:
            # Log yoksa bir mesaj göster
            no_log_label = Gtk.Label(label="No terminal output recorded for this application.")
            no_log_label.set_margin_start(16)
            no_log_label.set_margin_top(8)
            no_log_label.set_margin_bottom(8)
            no_log_label.set_xalign(0)  # Left align
            
            expander.add_row(no_log_label)
        
        self.results_list_box.append(expander)
    
    # Özet bilgisini güncelle
    total = working_count + not_working_count + skipped_count
    self.summary_label.set_text(f"Total: {total} APKs | Working: {working_count} | Not Working: {not_working_count} | Skipped: {skipped_count}")

def on_new_test_clicked(self, button):
    # Yeni bir test için başlangıç sayfasına dön
    self.welcome_view.set_visible(True)
    self.results_view.set_visible(False)
    self.testing_view.set_visible(False)
    
    # Değişkenleri sıfırla
    self.current_apk_index = 0
    self.apk_files = []
    self.test_results = {}

def on_export_clicked(self, button):
    # Dosya kaydetme diyaloğu
    file_dialog = Gtk.FileDialog()
    file_dialog.set_title("Save Results")
    file_dialog.set_initial_name("android_translation_layer_results.txt")
    
    # Filtre ekle
    text_filter = Gtk.FileFilter()
    text_filter.set_name("Text Files")
    text_filter.add_mime_type("text/plain")
    
    # Diyaloğu göster
    file_dialog.save(self, None, self.on_export_dialog_response)

def on_export_dialog_response(self, dialog, result):
    try:
        file = dialog.save_finish(result)
        if file:
            path = file.get_path()
            self.export_results_to_file(path)
            
            # Başarı bildirimi
            toast = Adw.Toast.new(f"Results exported to: {path}")
            toast.set_timeout(5)
            self.toast_overlay.add_toast(toast)
    except Exception as e:
        # Hata bildirimi
        print(f"Error saving file: {e}")
        toast = Adw.Toast.new(f"Could not export results: {str(e)}")
        self.toast_overlay.add_toast(toast)

def export_results_to_file(self, file_path):
    # Çalışma zamanı bilgisi
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Özet sayıları hesapla
    working_count = sum(1 for result in self.test_results.values() if result == "working")
    not_working_count = sum(1 for result in self.test_results.values() if result == "not_working")
    skipped_count = sum(1 for result in self.test_results.values() if result == "skipped")
    total = len(self.test_results)
    
    with open(file_path, 'w') as f:
        # Başlık ve tarih
        f.write("===== ANDROID TRANSLATION LAYER - APPLICATION RESULTS =====\n")
        f.write(f"Date: {date_str}\n\n")
        
        # Özet
        f.write("===== SUMMARY =====\n")
        f.write(f"Total Applications: {total}\n")
        f.write(f"Working: {working_count}\n")
        f.write(f"Not Working: {not_working_count}\n")
        f.write(f"Skipped: {skipped_count}\n\n")
        
        # Detaylı sonuçlar
        f.write("===== DETAILED RESULTS =====\n")
        
        for apk_path, result in self.test_results.items():
            apk_name = os.path.basename(apk_path)
            result_text = "Working" if result == "working" else "Not Working" if result == "not_working" else "Skipped"
            f.write(f"{apk_name}: {result_text}\n") 