import io
import json
from PIL import Image
from pathlib import Path
import base64
import shutil

# characters_folder = 'Characters'
# cards_folder = 'Cards'
# characters = []
# update_name = "n"
# bot.char_image = ""
# bot.char_name = ""

# def upload_character(json_file, img, tavern=False):
#     json_file = json_file if type(json_file) == str else json_file.decode('utf-8')
#     data = json.loads(json_file)
#     outfile_name = data["char_name"]
#     i = 1
#     while Path(f'{characters_folder}/{outfile_name}.json').exists():
#         outfile_name = f'{data["char_name"]}_{i:03d}'
#         i += 1
#     if tavern:
#         outfile_name = f'TavernAI-{outfile_name}'
#     with open(Path(f'{characters_folder}/{outfile_name}.json'), 'w') as f:
#         f.write(json_file)
#     if img is not None:
#         img = Image.open(io.BytesIO(img))
#         img.save(Path(f'{characters_folder}/{outfile_name}.png'))
#     print(f'New character saved to "{characters_folder}/{outfile_name}.json".')
#     return outfile_name


# def upload_tavern_character(img, name1, name2):
#     _img = Image.open(io.BytesIO(img))
#     _img.getexif()
#     decoded_string = base64.b64decode(_img.info['chara'])
#     _json = json.loads(decoded_string)
#     _json = {"char_name": _json['name'], "char_persona": _json['description'], "char_greeting": _json["first_mes"], "example_dialogue": _json['mes_example'], "world_scenario": _json['scenario']}
#     _json['example_dialogue'] = _json['example_dialogue'].replace('{{user}}', name1).replace('{{char}}', _json['char_name'])
#     return upload_character(json.dumps(_json), img, tavern=True)


# def convert_card_to_character(card_filepath: Path, characters_folder: Path):
#     """Converts a single card to a character and returns the character data."""
#     with card_filepath.open('rb') as img_file:
#         img_data = img_file.read()
#         name1 = 'User'
#         name2 = 'Character'
#         tavern_character_data = upload_tavern_character(img_data, name1, name2)

#     character_filepath = characters_folder / f"{tavern_character_data}.json"
#     with character_filepath.open() as character_file:
#         character_data = json.load(character_file)

#     return character_data

# def convert_cards_to_characters(cards_folder: Path, characters_folder: Path):
#     """Converts all cards in the cards folder to characters."""
#     converted_folder = cards_folder / "Converted"
#     converted_folder.mkdir(exist_ok=True)

#     for card_filepath in cards_folder.glob("*.png"):
#         character_data = convert_card_to_character(card_filepath, characters_folder)
#         card_filepath.rename(converted_folder / card_filepath.name)
        
#     return character_data

# def load_characters_from_folder(characters_folder: Path):
#     """Loads character data from all JSON files in the characters folder."""
#     characters = []
#     for character_filepath in characters_folder.glob("*.json"):
#         with character_filepath.open(encoding="utf-8") as character_file:
#             character_data = json.load(character_file)
#             character_data['char_filename'] = character_filepath.name
#             image_filepath_jpg = character_filepath.with_suffix(".jpg")
#             image_filepath_png = character_filepath.with_suffix(".png")
#             if image_filepath_jpg.exists():
#                 character_data['char_image'] = image_filepath_jpg.name
#             elif image_filepath_png.exists():
#                 character_data['char_image'] = image_filepath_png.name
#             characters.append(character_data)
#     return characters

# def prompt_for_character_selection(characters):
#     """Prompts the user to select a character from the provided list."""
#     for i, character in enumerate(characters, start=1):
#         print(f"{i}. {character['char_name']}")
#     while True:
#         try:
#             selected_index = int(input(f"\nPlease select a character: ")) - 1
#             return characters[selected_index]
#         except (ValueError, IndexError):
#             print(f"Invalid input. Please enter a number between 1 and {len(characters)}.")


# def select_character(characters):
#     global update_name
#     """Allows the user to select a character"""
#     if Path("chardata.json").exists():
#         with open("chardata.json", encoding='utf-8') as character_file:
#             character_data = json.load(character_file)
#         print(f"Last Character used: {character_data['char_name']}")
#         answer = input(f"\nUse this character? (y/n) [y]: ") or "y"
#     else:
#         answer = "n"

#     if answer.lower() == "n":
#         character_data = prompt_for_character_selection(characters)
#         while True:
#             update_name = input("Update Bot name and pic? (y or n): ").lower()
#             if update_name in {"y", "n"}:
#                 break
#             print("Invalid input. Please enter 'y' or 'n'.")
#         if update_name == "y":
#             bot.char_name = character_data["char_name"]
#             char_filename = character_data['char_filename']
#             bot.char_image = character_data.get("char_image")
#             shutil.copyfile(char_filename, "chardata.json")
#     return character_data

# # original on message
# # on ready event that will update the character name and picture if you chose yes
# # @bot.event
# # async def on_ready():
# #     global update_name
# #     if update_name.lower() == "y":
# #         try:
# #             with open(f"Characters/{bot.char_image}", 'rb') as f:
# #                 avatar_data = f.read()
# #             await bot.user.edit(username=bot.char_name, avatar=avatar_data)
# #         except FileNotFoundError:
# #             with open(f"Characters/default.png", 'rb') as f:
# #                 avatar_data = f.read()
# #             await bot.user.edit(username=bot.char_name, avatar=avatar_data)
# #             print(f"No image found for {bot.char_name}. Setting image to default.")
# #         except discord.errors.HTTPException as error:
# #             if error.code == 50035 and 'Too many users have this username, please try another' in error.text:
# #                 new_name = input('Too many users have this username, Enter a new name(tip: üse án àccent lèttèr ): ')
# #                 await bot.user.edit(username=new_name, avatar=avatar_data)
# #             elif error.code == 50035 and 'You are changing your username or Discord Tag too fast. Try again later.' in error.text:
# #                 pass
# #             else:
# #                 raise error
