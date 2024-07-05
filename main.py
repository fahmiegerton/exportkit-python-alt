import os
import shutil
import json
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox, Frame, Toplevel
from tkinterdnd2 import DND_FILES, TkinterDnD
from psd_tools import PSDImage
from PIL import Image
from threading import Thread

class PSDConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PSD to JSON Converter")

        self.drop_frame = Frame(root, width=400, height=100, bd=2, relief='sunken')
        self.drop_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        self.label = Label(self.drop_frame, text="Drag and drop a PSD file here or browse to select")
        self.label.place(relx=0.5, rely=0.5, anchor='center')

        Label(root, text="PSD File (without extension):").grid(row=1, column=0, padx=10, pady=10)
        self.psd_entry = Entry(root, width=30)
        self.psd_entry.grid(row=1, column=1, padx=10, pady=10)

        Label(root, text="Output Folder Name:").grid(row=2, column=0, padx=10, pady=10)
        self.output_entry = Entry(root, width=30)
        self.output_entry.grid(row=2, column=1, padx=10, pady=10)

        Button(root, text="Browse", command=self.browse_psd).grid(row=1, column=2, padx=10, pady=10)
        Button(root, text="Convert", command=self.convert).grid(row=3, column=0, columnspan=3, pady=10)

    def on_drop(self, event):
        file_path = event.data
        if file_path.endswith('.psd'):
            self.psd_entry.delete(0, 'end')
            self.psd_entry.insert(0, os.path.splitext(os.path.basename(file_path))[0])
        else:
            messagebox.showerror("Error", "Please drop a valid PSD file.")

    def browse_psd(self):
        file_path = filedialog.askopenfilename(filetypes=[("PSD files", "*.psd")])
        if file_path:
            self.psd_entry.delete(0, 'end')
            self.psd_entry.insert(0, os.path.splitext(os.path.basename(file_path))[0])

    def convert(self):
        psd_filename = self.psd_entry.get().strip()
        output_folder = self.output_entry.get().strip()

        if not psd_filename or not output_folder:
            messagebox.showerror("Error", "Please provide both PSD file name and output folder name.")
            return

        psd_path = f"./assets/{psd_filename}.psd"
        output_path = f"./result/{output_folder}/"
        json_path = os.path.join(output_path, f"{output_folder}.json")
        skins_path = os.path.join(output_path, "skins/")

        if not os.path.exists(psd_path):
            messagebox.showerror("Error", f"The file {psd_path} does not exist.")
            return

        if os.path.exists(output_path):
            save_in_existing = messagebox.askyesno("Folder Exists", f"The folder {output_path} already exists. Do you want to save into that folder anyway?")
            if not save_in_existing:
                messagebox.showinfo("Operation Cancelled", "Please run the app again with a different name for the output folder.")
                return

        os.makedirs(skins_path, exist_ok=True)

        if os.path.exists(json_path):
            overwrite = messagebox.askyesno("File Exists", f"The file {json_path} already exists. Do you want to replace it?")
            if not overwrite:
                messagebox.showinfo("Operation Cancelled", "Operation cancelled.")
                return

        self.show_loading_indicator()
        Thread(target=self.process_psd, args=(psd_path, json_path, skins_path)).start()

    def show_loading_indicator(self):
        self.loading_window = Toplevel(self.root)
        self.loading_window.title("Processing")
        Label(self.loading_window, text="Processing, please wait...").pack(padx=20, pady=20)
        
    def process_psd(self, psd_path, json_path, skins_path):
        psd = PSDImage.open(psd_path)

        def extract_layers(layers):
            layer_data = []
            for layer in layers:
                if layer.is_group():
                    layer_data.extend(extract_layers(layer))
                else:
                    layer_info = {
                        "name": layer.name,
                        "x": int(layer.left),
                        "y": int(layer.top),
                        "width": int(layer.width),
                        "height": int(layer.height),
                        "type": "text" if layer.kind == 'type' else "image"
                    }
                    if layer.kind == 'type':
                        try:
                            text = layer.text
                            engine_dict = layer.engine_dict

                            style_run = engine_dict.get('StyleRun', {}).get('RunArray', [{}])[0].get('StyleSheet', {}).get('StyleSheetData', {})

                            font_set = engine_dict.get('ResourceDict', {}).get('FontSet', [])
                            font_index = style_run.get('Font', 0)
                            font_name = font_set[font_index]['Name'] if font_set and font_index < len(font_set) else "Font not found"

                            justification = engine_dict.get('ParagraphRun', {}).get('RunArray', [{}])[0].get('ParagraphSheet', {}).get('Properties', {}).get('Justification', "left")
                            if isinstance(justification, str):
                                justification = justification.lower()
                            else:
                                justification = "left"

                            line_height = style_run.get('Leading', 0)
                            color = style_run.get('FillColor', {}).get('Values', [0, 0, 0])
                            color_hex = f"0x{int(color[1]*255):02X}{int(color[2]*255):02X}{int(color[3]*255):02X}" if color else "0x000000"
                            size = style_run.get('FontSize', 0)
                            text_value = layer.text or ""

                            if font_name == "Font not found":
                                font_name = self.ask_font_name(layer.name)

                            layer_info.update({
                                "font": font_name,
                                "justification": justification,
                                "lineHeight": int(line_height),
                                "color": color_hex,
                                "size": int(size),
                                "text": text_value
                            })
                        except KeyError as e:
                            print(f"Error extracting text properties for layer '{layer.name}': Missing key {e}")
                        except Exception as e:
                            print(f"Unexpected error extracting text properties for layer '{layer.name}': {e}")
                    else:
                        image = layer.composite()
                        image_path = os.path.join(skins_path, f"{layer.name}.png")
                        image.save(image_path)
                        layer_info["src"] = f"./skins/{layer.name}.png"
                    layer_data.append(layer_info)
            return layer_data

        layers_data = extract_layers(psd)

        psd_data = {
            "name": os.path.splitext(os.path.basename(psd_path))[0],
            "path": os.path.basename(os.path.dirname(json_path)) + "/",
            "info": {
                "description": "Normal",
                "file": os.path.basename(psd_path),
                "date": "sRGB",
                "title": "",
                "author": "",
                "keywords": "",
                "generator": "Idk export kit"
            },
            "layers": layers_data
        }

        os.makedirs(skins_path, exist_ok=True)

        with open(json_path, 'w') as json_file:
            json.dump(psd_data, json_file, indent=4)

        self.loading_window.destroy()
        messagebox.showinfo("Success", f"JSON file saved to {json_path}")

    def ask_font_name(self, layer_name):
        from tkinter import simpledialog
        newWin = Tk()
        newWin.withdraw()
        retVal = simpledialog.askstring("Font Not Found", f"Font not found for layer '{layer_name}'. Please enter the font (e.g. Montserrat-Bold): " ,parent=newWin)
        newWin.destroy()
        return retVal

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = PSDConverterApp(root)
    root.mainloop()
