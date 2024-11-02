import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS, GPSTAGS
import webbrowser
import os
from datetime import datetime
import json
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time

class Logger:
    """Classe pour gérer les logs de l'application"""
    @staticmethod
    def log_error(error_message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[ERROR] {timestamp} - {error_message}")

    @staticmethod
    def log_info(info_message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[INFO] {timestamp} - {info_message}")

class ImageReverseSearch:
    """Classe pour gérer la recherche inverse d'images"""
    def __init__(self):
        self.driver = None
        self.logger = Logger()

    def init_driver(self):
        """Initialise le driver Chrome avec une configuration optimisée"""
        if not self.driver:
            try:
                options = webdriver.ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--disable-notifications')
                options.add_argument('--disable-extensions')
                options.add_argument('--ignore-certificate-errors')
                options.add_argument('--disable-infobars')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                self.driver.implicitly_wait(10)
                self.logger.log_info("Driver Chrome initialisé avec succès")

            except Exception as e:
                self.logger.log_error(f"Erreur d'initialisation du driver: {str(e)}")
                raise

    def search_image(self, image_path, callback):
        """Effectue la recherche inverse d'image"""
        try:
            self.init_driver()
            self.logger.log_info("Début de la recherche inverse")
            
            # Accès à Google Images
            self.driver.get("https://images.google.com/imghp")
            time.sleep(2)

            # Recherche et clic sur le bouton de recherche par image
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label='Recherche par image']"))
            )
            search_button.click()
            time.sleep(1)

            # Upload de l'image
            file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            abs_path = os.path.abspath(image_path)
            self.logger.log_info(f"Envoi de l'image: {abs_path}")
            file_input.send_keys(abs_path)

            # Attente des résultats
            time.sleep(5)
            
            # Extraction des résultats
            results = self.extract_results()
            callback(results)

        except Exception as e:
            error_msg = f"Erreur lors de la recherche: {str(e)}"
            self.logger.log_error(error_msg)
            callback({"error": error_msg})

        finally:
            self.close()

    def extract_results(self):
        """Extrait les informations pertinentes des résultats de recherche"""
        results = {
            "locations": [],
            "sites": [],
            "descriptions": []
        }

        try:
            # Extraction des différents éléments
            elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".g"))
            )

            for element in elements[:5]:
                try:
                    # Extraction du texte
                    text = element.text.strip()
                    if text:
                        results["descriptions"].append(text)

                    # Extraction des liens
                    links = element.find_elements(By.CSS_SELECTOR, "a")
                    for link in links:
                        url = link.get_attribute("href")
                        if url and url not in results["sites"]:
                            results["sites"].append(url)

                except Exception as e:
                    self.logger.log_error(f"Erreur lors de l'extraction d'un élément: {str(e)}")
                    continue

        except Exception as e:
            self.logger.log_error(f"Erreur lors de l'extraction des résultats: {str(e)}")

        return results

    def close(self):
        """Ferme proprement le driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.log_info("Driver fermé avec succès")
            except Exception as e:
                self.logger.log_error(f"Erreur lors de la fermeture du driver: {str(e)}")

class MetadataExtractor:
    """Classe pour gérer l'extraction des métadonnées"""
    def __init__(self):
        self.logger = Logger()

    def extract_metadata(self, image_path):
        """Extrait toutes les métadonnées d'une image"""
        try:
            metadata = {
                "file_info": self.get_file_info(image_path),
                "image_info": self.get_image_info(image_path),
                "exif_info": self.get_exif_info(image_path)
            }
            return metadata
        except Exception as e:
            self.logger.log_error(f"Erreur lors de l'extraction des métadonnées: {str(e)}")
            raise

    def get_file_info(self, image_path):
        """Récupère les informations du fichier"""
        try:
            file_stat = os.stat(image_path)
            return {
                "filename": os.path.basename(image_path),
                "size": self.format_file_size(file_stat.st_size),
                "created": datetime.fromtimestamp(file_stat.st_ctime).strftime('%d/%m/%Y %H:%M:%S'),
                "modified": datetime.fromtimestamp(file_stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S'),
                "path": os.path.abspath(image_path)
            }
        except Exception as e:
            self.logger.log_error(f"Erreur lors de la récupération des infos fichier: {str(e)}")
            raise

    def get_image_info(self, image_path):
        """Récupère les informations techniques de l'image"""
        try:
            with Image.open(image_path) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "size": f"{img.width} x {img.height}",
                    "dpi": img.info.get('dpi', 'Non spécifié')
                }
        except Exception as e:
            self.logger.log_error(f"Erreur lors de la récupération des infos image: {str(e)}")
            raise

    def get_exif_info(self, image_path):
        """Récupère les métadonnées EXIF"""
        try:
            with Image.open(image_path) as img:
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag_id in exif:
                        tag = TAGS.get(tag_id, tag_id)
                        data = exif[tag_id]
                        if isinstance(data, bytes):
                            data = data.decode(errors='replace')
                        exif_data[tag] = data

                    # Traitement spécial pour les données GPS
                    if 'GPSInfo' in exif_data:
                        gps_info = self.process_gps_data(exif_data['GPSInfo'])
                        if gps_info:
                            exif_data['GPS'] = gps_info

                return exif_data
        except Exception as e:
            self.logger.log_error(f"Erreur lors de la récupération des infos EXIF: {str(e)}")
            return {}

    def process_gps_data(self, gps_info):
        """Traite les données GPS"""
        try:
            gps_data = {}
            for key in gps_info.keys():
                decode = GPSTAGS.get(key, key)
                gps_data[decode] = gps_info[key]

            lat = self.convert_to_degrees(gps_data.get('GPSLatitude'))
            lat_ref = gps_data.get('GPSLatitudeRef', 'N')

            lon = self.convert_to_degrees(gps_data.get('GPSLongitude'))
            lon_ref = gps_data.get('GPSLongitudeRef', 'E')

            if all([lat, lon]):
                if lat_ref == 'S': lat = -lat
                if lon_ref == 'W': lon = -lon
                return {'latitude': lat, 'longitude': lon}

        except Exception as e:
            self.logger.log_error(f"Erreur lors du traitement GPS: {str(e)}")
            return None

    @staticmethod
    def convert_to_degrees(values):
        """Convertit les coordonnées GPS en degrés décimaux"""
        if not values:
            return None

        try:
            d, m, s = [float(x) for x in values]
            return d + (m / 60.0) + (s / 3600.0)
        except:
            return None

    @staticmethod
    def format_file_size(size):
        """Formate la taille du fichier"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

class MetadataExtractorGUI:
    """Classe principale de l'interface graphique"""
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # Instances des classes utilitaires
        self.metadata_extractor = MetadataExtractor()
        self.reverse_search = ImageReverseSearch()
        self.logger = Logger()

        # Variables d'instance
        self.current_image_path = None
        self.current_metadata = None

        # Configuration de l'interface
        self.setup_styles()
        self.create_widgets()
        self.setup_grid_weights()

    def setup_window(self):
        """Configure la fenêtre principale"""
        self.root.title("Extracteur de Métadonnées Avancé")
        width = 1000
        height = 800
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(800, 600)

    def setup_styles(self):
        """Configure les styles de l'interface"""
        style = ttk.Style()
        style.configure('TButton', padding=5)
        style.configure('TLabel', padding=5)
        style.configure('Header.TLabel', font=('Helvetica', 14, 'bold'))
        style.configure('Section.TLabel', font=('Helvetica', 11, 'bold'))
        style.configure('Info.TLabel', font=('Helvetica', 10))

    def create_widgets(self):
        """Crée tous les widgets de l'interface"""
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # En-tête
        self.create_header()

        # Conteneur principal
        content_frame = ttk.Frame(self.main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        content_frame.grid_columnconfigure(1, weight=1)

        # Panneau gauche (aperçu)
        self.create_preview_panel(content_frame)

        # Panneau droit (métadonnées)
        self.create_metadata_panel(content_frame)

        # Barre de statut
        self.create_status_bar()

    def create_header(self):
        """Crée la section d'en-tête"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky="ew")

        title = ttk.Label(
            header_frame,
            text="Analyseur de Métadonnées et Recherche d'Images",
            style='Header.TLabel'
        )
        title.pack(pady=10)

        select_btn = ttk.Button(
            header_frame,
            text="Sélectionner une image",
            command=self.select_image,
            width=25
        )
        select_btn.pack(pady=5)

    def create_preview_panel(self, parent):
        """Crée le panneau d'aperçu"""
        preview_frame = ttk.LabelFrame(parent, text="Aperçu", padding="10")
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(expand=True, fill="both")

        # Boutons d'action
        button_frame = ttk.Frame(preview_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        self.maps_btn = ttk.Button(
            button_frame,
            text="Ouvrir dans Google Maps",
            command=self.open_in_maps,
            state="disabled"
        )
        self.maps_btn.pack(side="left", padx=5)

        self.reverse_search_btn = ttk.Button(
            button_frame,
            text="Recherche inverse",
            command=self.start_reverse_search,
            state="disabled"
        )
        self.reverse_search_btn.pack(side="left", padx=5)
    def create_metadata_panel(self, parent):
        """Crée le panneau des métadonnées"""
        metadata_frame = ttk.LabelFrame(parent, text="Informations et Métadonnées", padding="10")
        metadata_frame.grid(row=0, column=1, sticky="nsew")
        
        # Zone de texte avec scrollbar
        self.metadata_text = tk.Text(
            metadata_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            padx=10,
            pady=10
        )
        scrollbar = ttk.Scrollbar(
            metadata_frame,
            orient="vertical",
            command=self.metadata_text.yview
        )
        
        self.metadata_text.configure(yscrollcommand=scrollbar.set)
        self.metadata_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_status_bar(self):
        """Crée la barre de statut"""
        self.status_var = tk.StringVar(value="Prêt")
        self.status_label = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            style='Info.TLabel'
        )
        self.status_label.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def setup_grid_weights(self):
        """Configure le redimensionnement de la grille"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def select_image(self):
        """Gère la sélection d'une image"""
        filetypes = (
            ("Images", "*.jpg;*.jpeg;*.png;*.tiff;*.bmp;*.gif"),
            ("JPEG", "*.jpg;*.jpeg"),
            ("PNG", "*.png"),
            ("Tous les fichiers", "*.*")
        )
        
        try:
            filename = filedialog.askopenfilename(
                title="Sélectionner une image",
                filetypes=filetypes
            )
            
            if filename:
                self.current_image_path = filename
                self.load_image()
                self.extract_and_display_metadata()
                self.reverse_search_btn.configure(state="normal")
                self.status_var.set("Image chargée avec succès")
                
        except Exception as e:
            self.logger.log_error(f"Erreur lors de la sélection de l'image: {str(e)}")
            messagebox.showerror("Erreur", "Impossible de charger l'image sélectionnée")

    def load_image(self):
        """Charge et affiche l'aperçu de l'image"""
        try:
            image = Image.open(self.current_image_path)
            
            # Calcul des dimensions pour l'aperçu
            display_size = (350, 350)
            image.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # Conversion pour Tkinter
            photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo  # Garde une référence
            
        except Exception as e:
            self.logger.log_error(f"Erreur lors du chargement de l'image: {str(e)}")
            raise

    def extract_and_display_metadata(self):
        """Extrait et affiche les métadonnées de l'image"""
        try:
            self.metadata_text.delete(1.0, tk.END)
            metadata = self.metadata_extractor.extract_metadata(self.current_image_path)
            self.current_metadata = metadata
            
            # Affichage des informations du fichier
            self.display_section("INFORMATIONS DU FICHIER", metadata["file_info"])
            
            # Affichage des informations de l'image
            self.display_section("INFORMATIONS DE L'IMAGE", metadata["image_info"])
            
            # Affichage des métadonnées EXIF
            self.display_section("MÉTADONNÉES EXIF", metadata["exif_info"])
            
            # Active le bouton Google Maps si des coordonnées GPS sont présentes
            if "GPS" in metadata["exif_info"]:
                self.maps_btn.configure(state="normal")
            else:
                self.maps_btn.configure(state="disabled")
                
        except Exception as e:
            self.logger.log_error(f"Erreur lors de l'extraction des métadonnées: {str(e)}")
            self.metadata_text.insert(tk.END, "Erreur lors de l'extraction des métadonnées\n")

    def display_section(self, title, data):
        """Affiche une section de métadonnées"""
        width = 50
        self.metadata_text.insert(tk.END, "\n" + "=" * width + "\n")
        self.metadata_text.insert(tk.END, title.center(width) + "\n")
        self.metadata_text.insert(tk.END, "=" * width + "\n\n")
        
        if isinstance(data, dict):
            for key, value in data.items():
                self.metadata_text.insert(tk.END, f"{key}: {value}\n")
        else:
            self.metadata_text.insert(tk.END, str(data) + "\n")
        
        self.metadata_text.insert(tk.END, "\n")

    def start_reverse_search(self):
        """Lance la recherche inverse"""
        if not self.current_image_path:
            return
            
        self.status_var.set("Recherche inverse en cours...")
        self.reverse_search_btn.configure(state="disabled")
        self.metadata_text.insert(tk.END, "\nLancement de la recherche inverse...\n")
        
        def search_thread():
            try:
                self.reverse_search.search_image(
                    self.current_image_path,
                    self.handle_search_results
                )
            except Exception as e:
                self.root.after(0, self.handle_search_error, str(e))
                
        thread = threading.Thread(target=search_thread)
        thread.daemon = True
        thread.start()

    def handle_search_results(self, results):
        """Traite les résultats de la recherche inverse"""
        def update_ui():
            if "error" in results:
                self.handle_search_error(results["error"])
                return
                
            self.display_section("RÉSULTATS DE LA RECHERCHE INVERSE", {
                "Sites trouvés": "\n".join(results["sites"]) if results["sites"] else "Aucun",
                "Descriptions": "\n".join(results["descriptions"]) if results["descriptions"] else "Aucune"
            })
            
            self.status_var.set("Recherche terminée")
            self.reverse_search_btn.configure(state="normal")
            
        self.root.after(0, update_ui)

    def handle_search_error(self, error_message):
        """Gère les erreurs de recherche"""
        self.status_var.set("Erreur lors de la recherche")
        self.reverse_search_btn.configure(state="normal")
        self.metadata_text.insert(tk.END, f"\nErreur: {error_message}\n")
        
        messagebox.showerror(
            "Erreur",
            f"La recherche inverse a échoué: {error_message}"
        )

    def open_in_maps(self):
        """Ouvre les coordonnées dans Google Maps"""
        if not self.current_metadata:
            return
            
        try:
            gps_info = self.current_metadata["exif_info"].get("GPS")
            if gps_info:
                lat = gps_info["latitude"]
                lon = gps_info["longitude"]
                url = f"https://www.google.com/maps?q={lat},{lon}"
                webbrowser.open(url)
            else:
                messagebox.showinfo(
                    "Information",
                    "Aucune coordonnée GPS disponible pour cette image"
                )
        except Exception as e:
            self.logger.log_error(f"Erreur lors de l'ouverture de Google Maps: {str(e)}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir Google Maps")

    def run(self):
        """Lance l'application"""
        try:
            self.root.mainloop()
        finally:
            if self.reverse_search:
                self.reverse_search.close()

def main():
    """Point d'entrée du programme"""
    try:
        app = MetadataExtractorGUI()
        app.run()
    except Exception as e:
        Logger.log_error(f"Erreur fatale de l'application: {str(e)}")
        messagebox.showerror(
            "Erreur fatale",
            "Une erreur critique est survenue. L'application doit être fermée."
        )

if __name__ == "__main__":
    main()