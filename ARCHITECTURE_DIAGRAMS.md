# 🏗️ VillageCrop - Architecture Diagrams

Complete Mermaid flow diagrams for the VillageCrop application architecture.

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph Client["🖥️ Client Layer"]
        Web[Web Browser<br/>Flask Templates]
        React[React SPA<br/>agri-ai]
    end

    subgraph Backend["⚙️ Application Layer"]
        Flask[Flask Web Server<br/>Port 5000]
        Auth[Authentication<br/>Module]
        Pred[Prediction<br/>Module]
        Ollama[Ollama Service<br/>AI Insights]
        Farm[Farm Boundaries<br/>Module]
    end

    subgraph Services["🔧 Services"]
        ImgProc[Image Processing<br/>Blur Detection + CNN]
        OllamaAPI[Ollama LLM<br/>llama3.2]
    end

    subgraph Data["💾 Data Layer"]
        MongoDB[(MongoDB<br/>villagecrop)]
        Uploads[File Storage<br/>User Images]
        Models[ML Models<br/>best_model.pth]
    end

    Web --> Flask
    React --> Flask
    Flask --> Auth
    Flask --> Pred
    Flask --> Ollama
    Flask --> Farm
    Auth --> MongoDB
    Pred --> ImgProc
    Pred --> MongoDB
    ImgProc --> Models
    Ollama --> OllamaAPI
    Ollama --> MongoDB
    Farm --> MongoDB
    Pred --> Uploads
```

---

## 2. Data Flow - Prediction Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Flask
    participant Auth
    participant ImgProc
    participant CNN
    participant MongoDB
    participant Ollama

    User->>Frontend: Upload leaf image
    Frontend->>Flask: POST /predictions/api/predict
    Flask->>Auth: Verify session (user_id)
    Auth-->>Flask: Valid user_id

    Flask->>ImgProc: Process image
    ImgProc->>ImgProc: Blur detection<br/>(Laplacian variance)
    alt Image too blurry
        ImgProc-->>Flask: Reject: blurry image
        Flask-->>Frontend: Error 400
        Frontend-->>User: Request clear image
    else Image OK
        ImgProc->>CNN: Run prediction
        CNN-->>ImgProc: Disease + Confidence
        ImgProc-->>Flask: Prediction result
    end

    Flask->>MongoDB: Store prediction<br/>(with user_id link)
    MongoDB-->>Flask: prediction_id

    Flask->>MongoDB: Update user predictions array
    MongoDB-->>Flask: Success

    Flask-->>Frontend: JSON response
    Frontend-->>User: Display results

    Note over User,Ollama: Optional: Generate AI insights
    User->>Frontend: Request AI answers
    Frontend->>Flask: POST /ollama/api/generate
    Flask->>MongoDB: Get latest prediction
    MongoDB-->>Flask: Disease info
    Flask->>Ollama: Call Ollama API<br/>(4 prompts)
    Ollama-->>Flask: AI responses
    Flask->>MongoDB: Store responses
    MongoDB-->>Flask: Success
    Flask-->>Frontend: AI answers
    Frontend-->>User: Display expert advice
```

---

## 3. MongoDB Entity Relationship

```mermaid
erDiagram
    USERS ||--o{ PREDICTIONS : "makes"
    USERS {
        ObjectId _id PK
        string username UK
        string email UK
        string password "bcrypt hash"
        array predictions "embedded refs"
        object farm_boundaries "GeoJSON"
        datetime created_at
    }
    PREDICTIONS {
        ObjectId _id PK
        ObjectId user_id FK "→ users._id"
        string image_filename
        binary image_data "PNG binary"
        string disease
        float confidence
        float blur_variance
        boolean is_blurry
        string recommendation
        boolean processed
        array ollama_responses
        datetime timestamp
    }
```

---

## 4. CNN Model Architecture

```mermaid
graph TD
    subgraph Input["Input Layer"]
        I[224×224×3 RGB Image]
    end

    subgraph Features["Feature Extraction"]
        B1[Block 1: 3→32→32<br/>224→112<br/>ReLU + Dropout]
        B2[Block 2: 32→64→64<br/>112→56<br/>ReLU + Dropout]
        B3[Block 3: 64→128→128<br/>56→28<br/>ReLU + Dropout]
        B4[Block 4: 128→256→256<br/>28→14<br/>ReLU + Dropout]
        B5[Block 5: 256→512→512<br/>14→7<br/>ReLU + AdaptivePool]
    end

    subgraph Classifier["Classifier"]
        Flat[Flatten: 512×7×7 → 25088]
        FC1[FC: 25088→1024<br/>ReLU + Dropout 0.5]
        FC2[FC: 1024→18<br/>Softmax]
    end

    subgraph Output["Output"]
        O[18 Disease Classes]
    end

    I --> B1 --> B2 --> B3 --> B4 --> B5 --> Flat --> FC1 --> FC2 --> O

    style I fill:#e1f5fe
    style O fill:#c8e6c9
    style B1 fill:#fff3e0
    style B2 fill:#fff3e0
    style B3 fill:#fff3e0
    style B4 fill:#fff3e0
    style B5 fill:#fff3e0
```

---

## 5. Application Module Dependencies

```mermaid
graph LR
    subgraph Entry["Entry Point"]
        run[run.py]
    end

    subgraph App["Flask App Factory"]
        init[app/__init__.py<br/>create_app]
        config[app/config.py]
    end

    subgraph Routes["Route Blueprints"]
        auth[auth.py<br/>/auth/*]
        dash[dashboard.py<br/>/dashboard]
        pred[predictions.py<br/>/predictions/*]
        oll[ollama.py<br/>/ollama/*]
        farm[farm.py<br/>/farm/*]
    end

    subgraph Services["Services"]
        img[img_processor.py<br/>CNN + Blur]
        ollama[ollama_service.py<br/>LLM calls]
    end

    subgraph External["External"]
        mongo[(MongoDB)]
        model[best_model.pth]
        olli[Ollama API]
    end

    run --> init
    init --> config
    init --> auth
    init --> dash
    init --> pred
    init --> oll
    init --> farm

    auth --> mongo
    dash --> mongo
    pred --> img
    pred --> mongo
    oll --> ollama
    oll --> mongo
    farm --> mongo

    img --> model
    ollama --> olli
```

---

## 6. User Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant Flask
    participant MongoDB

    User->>Browser: Visit /auth/login
    Browser->>Flask: GET /auth/login
    Flask-->>Browser: Render login.html

    User->>Browser: Enter credentials
    Browser->>Flask: POST /auth/login
    Flask->>MongoDB: Find user by username
    MongoDB-->>Flask: User document

    Flask->>Flask: Verify password<br/>(bcrypt)
    alt Valid credentials
        Flask->>Flask: Create session<br/>session['user_id']
        Flask-->>Browser: Redirect to /dashboard
        Browser-->>User: Show dashboard
    else Invalid credentials
        Flask-->>Browser: Flash error message
        Browser-->>User: Show error
    end
```

---

## 7. Image Processing Pipeline

```mermaid
flowchart LR
    subgraph Input["Input"]
        IMG[Uploaded Image]
    end

    subgraph Preprocess["Preprocessing"]
        Resize[Resize to 224×224]
        Norm[Normalize RGB<br/>ImageNet stats]
        Tensor[Convert to Tensor]
    end

    subgraph Quality["Quality Check"]
        Gray[Convert to Grayscale]
        Lap[Laplacian Transform]
        Var[Calculate Variance]
        Check{Variance > 100?}
    end

    subgraph CNN["CNN Inference"]
        F1[Feature Block 1]
        F2[Feature Block 2]
        F3[Feature Block 3]
        F4[Feature Block 4]
        F5[Feature Block 5]
        Class[Classifier Head]
    end

    subgraph Output["Output"]
        Disease[Disease Class]
        Conf[Confidence Score]
        Rec[Recommendation]
    end

    IMG --> Resize --> Norm --> Tensor
    IMG --> Gray --> Lap --> Var --> Check
    Check -->|Pass| Tensor
    Check -->|Fail| Reject[Reject: Too Blurry]
    
    Tensor --> F1 --> F2 --> F3 --> F4 --> F5 --> Class
    Class --> Disease --> Conf --> Rec

    style IMG fill:#e1f5fe
    style Reject fill:#ffcdd2
    style Disease fill:#c8e6c9
    style Conf fill:#c8e6c9
    style Rec fill:#c8e6c9
```

---

## 8. Complete User Journey

```mermaid
journey
    title VillageCrop User Journey
    section Registration
      Visit website: 5: User
      Register account: 4: User
      Verify credentials: 5: System
    section Login
      Enter credentials: 5: User
      Session created: 5: System
      Redirect to dashboard: 5: System
    section Upload & Predict
      Navigate to upload: 5: User
      Select leaf image: 5: User
      Upload for analysis: 5: User
      Blur detection: 5: System
      CNN prediction: 5: System
      Store in MongoDB: 5: System
      Show results: 5: System
    section AI Insights
      View AI answers: 4: User
      Generate responses: 3: User
      Ollama processes: 4: System
      Display expert advice: 5: System
    section History
      View prediction history: 5: User
      Filter by date: 4: User
      Download results: 4: User
```

---

## 9. Component Architecture (React Frontend)

```mermaid
flowchart TB
    subgraph App["agri-ai React App"]
        Router[React Router]
        
        subgraph Pages["Pages"]
            Home[Home.jsx<br/>Upload & Analyze]
            Login[Login.jsx<br/>Authentication]
            Dash[Dashboard.jsx<br/>User Dashboard]
            Signup[Signup.jsx<br/>Registration]
        end

        subgraph Components["Shared Components"]
            Nav[Navigation]
            Card[Result Card]
            Upload[Upload Widget]
            Chart[Confidence Chart]
        end
    end

    subgraph API["Backend API"]
        Flask[Flask:5000]
        Endpoints[REST Endpoints]
    end

    App --> Router
    Router --> Home
    Router --> Login
    Router --> Dash
    Router --> Signup

    Home --> Upload
    Home --> Card
    Dash --> Chart
    Dash --> Nav

    Home --> API
    Login --> API
    Dash --> API
    Signup --> API
```

---

## 10. Disease Classification Hierarchy

```mermaid
mindmap
  root((18 Classes))
    Apple
      Apple scab
      Black rot
      Cedar apple rust
      Healthy
    Grape
      Black rot
      Esca
      Leaf blight
      Healthy
    Tomato
      Bacterial spot
      Early blight
      Late blight
      Leaf mold
      Septoria
      Spider mites
      Target spot
      YLCV
      Mosaic virus
      Healthy
```

---

## 11. Technology Stack Overview

```mermaid
quadrantChart
    title VillageCrop Technology Stack
    x-axis "Frontend" --> "Backend"
    y-axis "UI/UX" --> "Infrastructure"
    quadrant-1 "Application Layer"
    quadrant-2 "Presentation Layer"
    quadrant-3 "Data Layer"
    quadrant-4 "Services Layer"
    "Flask": [0.75, 0.25]
    "React": [0.25, 0.75]
    "MongoDB": [0.85, 0.15]
    "PyTorch": [0.80, 0.30]
    "Ollama": [0.90, 0.40]
    "OpenCV": [0.70, 0.35]
    "bcrypt": [0.65, 0.20]
    "Jinja2": [0.30, 0.70]
```

---

## 12. Deployment Architecture (Future)

```mermaid
flowchart TB
    subgraph Internet["🌐 Internet"]
        User[End Users]
    end

    subgraph CDN["📦 CDN Layer"]
        Static[Static Assets<br/>React Build]
    end

    subgraph LB["⚖️ Load Balancer"]
        Nginx[Nginx Reverse Proxy]
    end

    subgraph AppLayer["🔧 Application Layer"]
        Flask1[Flask Instance 1]
        Flask2[Flask Instance 2]
        Flask3[Flask Instance 3]
    end

    subgraph ServiceLayer["🛠️ Service Layer"]
        OllamaSvc[Ollama Service]
        Worker[Background Worker]
    end

    subgraph DataLayer["💾 Data Layer"]
        Mongo[(MongoDB Replica Set)]
        Redis[(Redis Cache)]
        S3[S3 Storage<br/>Images]
    end

    User --> CDN
    CDN --> LB
    LB --> Nginx
    Nginx --> Flask1
    Nginx --> Flask2
    Nginx --> Flask3
    Flask1 --> OllamaSvc
    Flask2 --> OllamaSvc
    Flask3 --> OllamaSvc
    Flask1 --> Mongo
    Flask2 --> Mongo
    Flask3 --> Mongo
    Flask1 --> Redis
    Flask2 --> Redis
    Flask3 --> Redis
    Flask1 --> S3
    Flask2 --> S3
    Flask3 --> S3
    Worker --> Mongo
    Worker --> S3
```

---

**Last Updated:** April 2026  
**Version:** 1.0
