# 🌐 KLIPPS Web Application

A web-based image matching system that connects to your KLIPPS backend API.

## 🚀 Features

- **📤 Image Upload**: Drag & drop or click to upload images
- **🔍 Image Matching**: Find matches in the KLIPPS database
- **📚 Database Viewer**: Browse all stored images
- **📊 Match Results**: View detailed match information with confidence scores
- **🎨 Modern UI**: Beautiful, responsive design

## 🛠️ Setup

### Prerequisites
- Python 3.7+
- Backend server running on `http://localhost:8000`

### Installation
1. **Start the backend server**:
   ```bash
   .\start_backend.bat
   ```

2. **Start the web application**:
   ```bash
   .\start_web_app.bat
   ```

3. **Open your browser** and go to:
   ```
   http://localhost:8080
   ```

## 📱 Usage

### Upload and Match Images
1. **Upload an image** by dragging and dropping or clicking "Choose Image"
2. **Click "Find Matches"** to search the database
3. **View results** with match confidence and details

### Browse Database
1. **Click "Refresh Database"** to load all stored images
2. **Browse through** all images in the database
3. **See business names** and PDF sources

## 🔧 API Endpoints Used

- `GET /api/images/` - Get all database images
- `POST /match-image/` - Match uploaded image
- `GET /images/{filename}` - Access image files

## 🎯 Features

### Image Matching
- ✅ **Upload any image format** (JPEG, PNG, etc.)
- ✅ **Automatic matching** against database
- ✅ **Confidence scores** for matches
- ✅ **Detailed match information**

### Database Management
- ✅ **View all stored images**
- ✅ **Business information** display
- ✅ **PDF source tracking**
- ✅ **Real-time updates**

### User Interface
- ✅ **Drag & drop** file upload
- ✅ **Image preview** before matching
- ✅ **Responsive design** for all devices
- ✅ **Status notifications** for all actions

## 🎨 Screenshots

The web app includes:
- **Modern gradient design**
- **Interactive upload area**
- **Match result cards**
- **Database image grid**
- **Status notifications**

## 🔗 Backend Integration

The web app connects to your existing KLIPPS backend:
- **Database**: SQLite with extracted images
- **API**: FastAPI with CORS support
- **Images**: Static file serving from `extracted_images/`

## 🚀 Quick Start

1. **Ensure backend is running** on port 8000
2. **Run the web app** with the batch file
3. **Open browser** to `http://localhost:8080`
4. **Upload an image** and find matches!

## 📊 Database Information

Your database contains:
- **15 extracted images** from PDFs
- **Business metadata** (names, references)
- **Image paths** pointing to PNG files
- **Page numbers** and file information

The web app will automatically load and display all this information! 