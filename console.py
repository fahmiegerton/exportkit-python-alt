from psd_tools import PSDImage
import json
import os
import shutil

# Prompt user for file names
psd_filename = input("Please enter the name of your PSD file (without extension): ")
output_folder = input("Please enter the name for the output folder: ")

# Construct paths
psd_path = f"./assets/{psd_filename}.psd"
output_path = f"./result/{output_folder}/"
json_path = os.path.join(output_path, f"{output_folder}.json")
skins_path = os.path.join(output_path, "skins/")

# Check if the output folder already exists
if os.path.exists(output_path):
    save_in_existing = input(f"The folder {output_path} already exists. Do you want to save into that folder anyway? (yes/no): ")
    if save_in_existing.lower() != 'yes':
        print("Please run the script again with a different name for the output folder.")
        exit()

# Ensure the result and skins directories exist
os.makedirs(skins_path, exist_ok=True)

# Check if JSON file already exists
if os.path.exists(json_path):
    overwrite = input(f"The file {json_path} already exists. Do you want to replace it? (yes/no): ")
    if overwrite.lower() != 'yes':
        print("Operation cancelled.")
        exit()

# Load the PSD file
psd = PSDImage.open(psd_path)

# Function to extract layer information
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
                    # Access text layer properties
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
                        font_name = input(f"Font not found for layer '{layer.name}'. Please enter the font (e.g. Montserrat-Bold): ")

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
                # Extract image layer
                image = layer.composite()
                image_path = os.path.join(skins_path, f"{layer.name}.png")
                image.save(image_path)
                layer_info["src"] = f"./skins/{layer.name}.png"
            layer_data.append(layer_info)
    return layer_data

# Extract data
layers_data = extract_layers(psd)

# Construct the JSON data structure
psd_data = {
    "name": psd_filename,
    "path": f"{output_folder}/",
    "info": {
        "description": "Normal",
        "file": psd_filename,
        "date": "sRGB",
        "title": "",
        "author": "",
        "keywords": "",
        "generator": "Idk export kit"
    },
    "layers": layers_data
}

# Save to JSON
with open(json_path, 'w') as json_file:
    json.dump(psd_data, json_file, indent=4)

print(f"JSON file saved to {json_path}")
