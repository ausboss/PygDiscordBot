import discord
from discord.ext import commands
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image, ImageTk 
from io import BytesIO
import torch
import requests
import re
from transformers import ViTFeatureExtractor, AutoTokenizer, VisionEncoderDecoderModel

class ImageCaptionCog(commands.Cog, name="image_caption"):
    def __init__(self, bot):
        self.bot = bot
        self.loc = "ydshieh/vit-gpt2-coco-en"
        self.feature_extractor = ViTFeatureExtractor.from_pretrained(self.loc)
        self.tokenizer = AutoTokenizer.from_pretrained(self.loc)
        self.model = VisionEncoderDecoderModel.from_pretrained(self.loc)
        self.model.eval()

    @commands.command(name="image_comment")
    async def image_comment(self, message: discord.Message, message_content) -> None:
        # Check if the message content is a URL
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        if url_pattern.match(message_content):
            # Download the image from the URL and convert it to a PIL image
            response = requests.get(message_content)
            image = Image.open(BytesIO(response.content)).convert('RGB')
        else:
            # Download the image from the message and convert it to a PIL image
            image_url = message.attachments[0].url
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content)).convert('RGB')
            
        # Generate the image caption
        caption = self.predict(image)
        message_content = f"{message_content} [{message.author.name} posts a picture of {caption}]"
        return message_content

    def predict(self, image):
        pixel_values = self.feature_extractor(images=image, return_tensors="pt").pixel_values
        with torch.no_grad():
            output_ids = self.model.generate(pixel_values, max_length=16, num_beams=4, return_dict_in_generate=True).sequences
        preds = self.tokenizer.batch_decode(output_ids, skip_special_tokens=True)
        preds = [pred.strip() for pred in preds]
        return preds[0]

async def setup(bot):
    await bot.add_cog(ImageCaptionCog(bot))
