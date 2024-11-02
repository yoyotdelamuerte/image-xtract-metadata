import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS, GPSTAGS
import webbrowser
import os
from datetime import datetime
import json

class MetadataExtractorGUI:
    def __init__(self):
        # Création de la fenêtre principale
        self.root = tk.Tk()
        self.root.title("Extracteur de Métadonnées")
        
        # Configuration de la taille et position
        self.setup_window()
        
        # Variables
        self.current_image_path = None
        self.image_preview = None
        self.coordinates = None
        
        # Configuration des styles
        self.setup_styles()
        
        # Création de l'interface
        self.create_widgets()
        
    def setup_window(self):
        """Configure la taille et la position de la fenêtre"""
        width = 900
        height = 700
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
        style.configure('Title.TLabel', font=('Helvetica', 11, 'bold'))
        
    def create_widgets(self):
        """Crée tous les éléments de l'interface"""
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        self.create_header()
        self.create_select_button()
        self.create_content_area()
        self.create_action_buttons()
        self.setup_grid_weights()
        
    def create_header(self):
        """Crée l'en-tête de l'application"""
        header = ttk.Label(
            self.main_frame,
            text="Analyseur de Métadonnées d'Images",
            style='Header.TLabel'
        )
        header.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
    def create_select_button(self):
        """Crée le bouton de sélection d'image"""
        select_frame = ttk.Frame(self.main_frame)
        select_frame.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        self.select_btn = ttk.Button(
            select_frame,
            text="Sélectionner une image",
            command=self.select_image,
            width=25
        )
        self.select_btn.pack(expand=True)
        
    def create_content_area(self):
        """Crée la zone principale de contenu"""
        # Frame de contenu
        content_frame = ttk.Frame(self.main_frame)
        content_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Zone d'aperçu
        self.create_preview_area(content_frame)
        
        # Zone de métadonnées
        self.create_metadata_area(content_frame)
        
    def create_preview_area(self, parent):
        """Crée la zone d'aperçu de l'image"""
        preview_container = ttk.LabelFrame(parent, text="Aperçu", padding="10")
        preview_container.grid(row=0, column=0, padx=5, sticky="nsew")
        
        self.preview_label = ttk.Label(preview_container)
        self.preview_label.pack(expand=True, fill="both")
        
    def create_metadata_area(self, parent):
        """Crée la zone d'affichage des métadonnées"""
        metadata_container = ttk.LabelFrame(
            parent, 
            text="Informations et Métadonnées",
            padding="10"
        )
        metadata_container.grid(row=0, column=1, padx=5, sticky="nsew")
        
        # Création de la zone de texte avec scrollbar
        text_frame = ttk.Frame(metadata_container)
        text_frame.pack(expand=True, fill="both")
        
        self.metadata_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            width=50,
            height=25,
            font=('Consolas', 10),
            padx=10,
            pady=10
        )
        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.metadata_text.yview
        )
        
        self.metadata_text.configure(yscrollcommand=scrollbar.set)
        self.metadata_text.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
    def create_action_buttons(self):
        """Crée les boutons d'action"""
        action_frame = ttk.Frame(self.main_frame)
        action_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        self.maps_btn = ttk.Button(
            action_frame,
            text="Ouvrir dans Google Maps",
            command=self.open_in_maps,
            state="disabled",
            width=25
        )
        self.maps_btn.pack(side="left", padx=5)
        
        save_btn = ttk.Button(
            action_frame,
            text="Sauvegarder les métadonnées",
            command=self.save_metadata,
            width=25
        )
        save_btn.pack(side="left", padx=5)
        
    def setup_grid_weights(self):
        """Configure le redimensionnement de la grille"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
    def select_image(self):
        """Gère la sélection d'une image"""
        filetypes = (
            ("Images", "*.jpg;*.jpeg;*.png;*.tiff;*.bmp;*.gif"),
            ("JPEG", "*.jpg;*.jpeg"),
            ("PNG", "*.png"),
            ("Tous les fichiers", "*.*")
        )
        
        filename = filedialog.askopenfilename(
            title="Sélectionner une image",
            filetypes=filetypes
        )
        
        if filename:
            self.current_image_path = filename
            self.load_image()
            self.extract_metadata()
            
    def load_image(self):
        """Charge et affiche l'aperçu de l'image"""
        try:
            image = Image.open(self.current_image_path)
            
            # Calcul des dimensions pour l'aperçu
            display_size = (350, 350)
            image.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger l'image: {str(e)}")
            
    def extract_metadata(self):
        """Extrait et affiche les métadonnées de l'image"""
        try:
            self.metadata_text.delete(1.0, tk.END)
            
            image = Image.open(self.current_image_path)
            file_info = os.stat(self.current_image_path)
            
            self.display_file_info(image, file_info)
            self.display_image_info(image)
            self.display_exif_info(image)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'extraction: {str(e)}")
            
    def display_file_info(self, image, file_info):
        """Affiche les informations du fichier"""
        self.add_section_header("INFORMATIONS DU FICHIER")
        info = {
            "Nom du fichier": os.path.basename(self.current_image_path),
            "Format": image.format,
            "Taille du fichier": self.format_file_size(file_info.st_size),
            "Date de création": datetime.fromtimestamp(file_info.st_ctime).strftime('%d/%m/%Y %H:%M:%S'),
            "Dernière modification": datetime.fromtimestamp(file_info.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
        }
        self.add_info_dict(info)
        
    def display_image_info(self, image):
        """Affiche les informations de l'image"""
        self.add_section_header("INFORMATIONS DE L'IMAGE")
        info = {
            "Dimensions": f"{image.size[0]} x {image.size[1]} pixels",
            "Mode couleur": image.mode,
            "Résolution": image.info.get('dpi', 'Non spécifiée')
        }
        self.add_info_dict(info)
        
    def display_exif_info(self, image):
        """Affiche les métadonnées EXIF"""
        self.add_section_header("MÉTADONNÉES EXIF")
        try:
            exif = image.getexif()
            if exif:
                for tag_id in exif:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exif.get(tag_id)
                    
                    if isinstance(data, bytes):
                        data = data.decode(errors='replace')
                        
                    if tag == 'GPSInfo':
                        gps_data = self.process_gps_data(data)
                        if gps_data:
                            self.coordinates = gps_data
                            self.metadata_text.insert(tk.END, 
                                f"GPS Latitude : {gps_data[0]}\n"
                                f"GPS Longitude : {gps_data[1]}\n")
                            self.maps_btn.configure(state="normal")
                    else:
                        self.metadata_text.insert(tk.END, f"{tag}: {data}\n")
            else:
                self.metadata_text.insert(tk.END, "Aucune métadonnée EXIF trouvée\n")
                self.maps_btn.configure(state="disabled")
        except Exception:
            self.metadata_text.insert(tk.END, "Erreur lors de la lecture des métadonnées EXIF\n")
            
    def add_section_header(self, text):
        """Ajoute un en-tête de section centré"""
        width = 50
        padding = (width - len(text)) // 2
        self.metadata_text.insert(tk.END, 
            "\n" + " " * padding + text + "\n" +
            "=" * width + "\n\n")
            
    def add_info_dict(self, info_dict):
        """Ajoute un dictionnaire d'informations formaté"""
        for key, value in info_dict.items():
            self.metadata_text.insert(tk.END, f"{key} : {value}\n")
        self.metadata_text.insert(tk.END, "\n")
        
    def format_file_size(self, size):
        """Formate la taille du fichier en unités lisibles"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
        
    def process_gps_data(self, gps_info):
        """Traite les données GPS"""
        try:
            gps_data = {}
            for key in gps_info.keys():
                decode = GPSTAGS.get(key, key)
                gps_data[decode] = gps_info[key]
                
            lat = self.convert_to_degrees(gps_data.get('GPSLatitude', None))
            lat_ref = gps_data.get('GPSLatitudeRef', 'N')
            
            lon = self.convert_to_degrees(gps_data.get('GPSLongitude', None))
            lon_ref = gps_data.get('GPSLongitudeRef', 'E')
            
            if all([lat, lon]):
                if lat_ref == 'S': lat = -lat
                if lon_ref == 'W': lon = -lon
                return (lat, lon)
                
        except Exception:
            return None
            
    def convert_to_degrees(self, values):
        """Convertit les coordonnées GPS en degrés décimaux"""
        if not values:
            return None
            
        try:
            d, m, s = map(float, values)
            return d + (m / 60.0) + (s / 3600.0)
        except Exception:
            return None
            
    def open_in_maps(self):
        """Ouvre les coordonnées dans Google Maps"""
        if self.coordinates:
            lat, lon = self.coordinates
            url = f"https://www.google.com/maps?q={lat},{lon}"
            webbrowser.open(url)
        else:
            messagebox.showwarning(
                "Attention",
                "Aucune coordonnée GPS disponible pour cette image"
            )
            
    def save_metadata(self):
        """Sauvegarde les métadonnées dans un fichier"""
        if not self.current_image_path:
            messagebox.showwarning(
                "Attention",
                "Veuillez d'abord sélectionner une image"
            )
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichier texte", "*.txt"), ("Tous les fichiers", "*.*")],
            initialfile="metadata_export.txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.metadata_text.get(1.0, tk.END))
                messagebox.showinfo(
                    "Succès",
                    "Les métadonnées ont été sauvegardées avec succès"
                )
            except Exception as e:
                messagebox.showerror(
                    "Erreur",
                    f"Erreur lors de la sauvegarde: {str(e)}"
                )
    
    def run(self):
        """Lance l'application"""
        self.root.mainloop()
        
def main():
    app = MetadataExtractorGUI()
    app.run()

if __name__ == "__main__":
    main()