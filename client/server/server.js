const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

const upload = multer({ dest: 'uploads/' });

// Тестовый маршрут для загрузки Excel
app.post('/upload', upload.single('file'), (req, res) => {
    console.log('Получен файл:', req.file);
    // Здесь будет обработка Excel → JSON
    res.json({ success: true, message: 'Файл получен', data: { tasks: [] } });
});

// Отдаём table.json
app.get('/tables.json', (req, res) => {
    res.sendFile(path.join(__dirname, 'tables.json'));
});

app.listen(PORT, () => {
    console.log(`✅ Тестовый сервер запущен: http://localhost:${PORT}`);
});