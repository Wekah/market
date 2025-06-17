const express = require("express");
const cors = require("cors");
const multer = require("multer");
const tf = require("@tensorflow/tfjs-node");
const mobilenet = require("@tensorflow-models/mobilenet");
const Jimp = require("jimp");
const path = require("path");

const app = express();
app.use(cors());

// Configure multer for file uploads
const upload = multer({ storage: multer.memoryStorage() });

let model;

// Load MobileNet model
async function loadModel() {
  model = await mobilenet.load({ version: 2, alpha: 1.0 });
  console.log("MobileNetV2 model loaded.");
}

app.get("/", (req, res) => {
  res.send("Image Recognition API is running.");
});

app.post("/recognize_image", upload.single("image"), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No image file provided" });
  }

  try {
    // Load and preprocess the image with Jimp
    const imageBuffer = req.file.buffer;
    const jimpImage = await Jimp.read(imageBuffer);
    jimpImage.resize(224, 224);
    const imageData = new Uint8Array(jimpImage.bitmap.data);

    const input = tf.node.decodeImage(imageData, 3)
      .expandDims(0)
      .toFloat()
      .div(tf.scalar(127.5))
      .sub(tf.scalar(1));

    // Predict using MobileNetV2
    const predictions = await model.classify(input);
    res.json({ predictions });

  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, async () => {
  await loadModel();
  console.log(`Server is running on port ${PORT}`);
});
