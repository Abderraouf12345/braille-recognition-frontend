import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Define NumberedCanvas for header, footer and page count
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Page 1 is the cover page - draw cover page background elements instead of header/footer
        if self._pageNumber == 1:
            # Draw a beautiful left decorative bar in navy blue
            self.setFillColor(colors.HexColor("#1E3A8A"))
            self.rect(0, 0, 30, 792, fill=True, stroke=False)
            
            # Draw a gold accent bar next to it
            self.setFillColor(colors.HexColor("#EAB308"))
            self.rect(30, 0, 6, 792, fill=True, stroke=False)
            
            # Draw some decorative geometric accents
            self.setFillColor(colors.HexColor("#EFF6FF"))
            self.rect(36, 700, 576, 92, fill=True, stroke=False)
            self.setFillColor(colors.HexColor("#1E3A8A"))
            self.setFont("Helvetica-Bold", 10)
            self.drawString(50, 746, "PROJECT DOCUMENTATION & TECHNICAL WHITE PAPER")
            self.restoreState()
            return
            
        # Running Headers & Footers for Pages 2+
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header text and thin divider line
        self.drawString(54, 750, "Braille Image Processing & Translation Portal — Technical Report")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 742, 612-54, 742)
        
        # Footer thin divider line and footer text
        self.line(54, 60, 612-54, 60)
        self.drawString(54, 45, "Confidential — Internal System Architecture Documentation")
        
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612-54, 45, page_text)
        self.restoreState()


def build_pdf(filename="project_explanation.pdf"):
    # Margins: 0.75 in (54 pt)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1E3A8A")   # Navy
    c_secondary = colors.HexColor("#2563EB") # Blue
    c_dark = colors.HexColor("#0F172A")      # Slate 900
    c_body = colors.HexColor("#334155")      # Slate 700
    c_accent = colors.HexColor("#EAB308")    # Gold
    c_bg_light = colors.HexColor("#F8FAFC")  # Light gray-blue
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=c_dark,
        spaceAfter=15,
        leftIndent=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#475569"),
        spaceAfter=30,
        leftIndent=10
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        leftIndent=10
    )
    
    h1_style = ParagraphStyle(
        'SecH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SecH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_secondary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'SecBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_body,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'SecBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    callout_style = ParagraphStyle(
        'SecCallout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=c_primary,
        backColor=colors.HexColor("#EFF6FF"),
        borderColor=colors.HexColor("#DBEAFE"),
        borderWidth=1,
        borderPadding=10,
        spaceBefore=8,
        spaceAfter=8
    )
    
    code_style = ParagraphStyle(
        'SecCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=c_dark,
        backColor=c_bg_light,
        borderWidth=0.5,
        borderColor=colors.HexColor("#E2E8F0"),
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=6
    )

    story = []
    
    # ------------------ COVER PAGE ------------------
    story.append(Spacer(1, 140))
    story.append(Paragraph("Braille Image Recognition &<br/>Translation Portal", title_style))
    story.append(Paragraph("An End-to-End Deep Learning & Computer Vision System for Automated Raised-Dot Decoding, Multi-Language Translation, AI Contextual Refinement, and Text-to-Speech Synthesis.", subtitle_style))
    
    # Decorative line
    d_table = Table([[""]], colWidths=[350], rowHeights=[2.5])
    d_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_accent),
        ('PADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(d_table)
    story.append(Spacer(1, 160))
    
    # Metadata block
    meta_text = """
    <b>Document Class:</b> Technical Whitepaper & System Architecture Guide<br/>
    <b>Target Domain:</b> Optical Braille Character Recognition (OBCR) & Assistive Tech<br/>
    <b>Deployment Environment:</b> FastAPI (Backend) & Next.js (React Frontend)<br/>
    <b>Date:</b> May 2026<br/>
    <b>Version:</b> 1.2.0 (Production-Ready)
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(PageBreak())
    
    # ------------------ PAGE 2: EXECUTIVE SUMMARY & ARCHITECTURE ------------------
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "This project implements a state-of-the-art web portal designed to recognize, transcribe, translate, and verbalize "
        "double-sided printed Braille documents from raw photographic images. The system targets a key challenge in assistive technology: "
        "enabling sighted educators, parents, and transcribers to quickly digitize physical Braille pages. The portal incorporates "
        "advanced computer vision algorithms to pre-process images, a custom PyTorch Convolutional Neural Network (CNN) to classify "
        "Braille dots, a rule-based multi-language translation engine, a Generative AI layer for spelling/contextual correction, "
        "and text-to-speech synthesis.",
        body_style
    ))
    
    story.append(Paragraph("2. System Architecture Overview", h1_style))
    story.append(Paragraph(
        "The system is divided into two distinct services communicating via JSON REST endpoints and Server-Sent Events (SSE) streaming:",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>• Frontend Dashboard (Next.js & TypeScript):</b> Provides a high-performance web workspace. Users upload images, "
        "interactively select document corners for perspective correction, and adjust light angles using a visual dial. It handles "
        "SSE streaming inputs for real-time visualization of processing stages and includes text-to-speech playback controls.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>• Computational Backend (FastAPI & PyTorch):</b> A Python-based microservice that executes heavy image warping, "
        "bilateral filtering, double adaptive thresholding, belief propagation grid alignment, CNN character classification, "
        "dictionary translation, Google Gemini Generative AI corrections, and text-to-speech generation.",
        bullet_style
    ))
    
    # Architecture Table
    arch_data = [
        [Paragraph("<b>Component / Layer</b>", body_style), Paragraph("<b>Technologies Used</b>", body_style), Paragraph("<b>Primary Functionality</b>", body_style)],
        [Paragraph("Client-Side UI", body_style), Paragraph("Next.js 16, React 19, TypeScript, Tailwind CSS, Lucide Icons, Framer Motion", body_style), Paragraph("Image workspace, interactive crop, real-time light visualizer, SSE streaming renderer, and TTS player.", body_style)],
        [Paragraph("Web Server", body_style), Paragraph("FastAPI, Uvicorn, Python Multiprocessing/ThreadPoolExecutor", body_style), Paragraph("Asynchronous endpoints, SSE progress stream, temporary file management, CORS middleware.", body_style)],
        [Paragraph("Computer Vision Pipeline", body_style), Paragraph("OpenCV, NumPy, SciPy (cKDTree), Numba (JIT)", body_style), Paragraph("Perspective warping, 4-pass tiled thresholding, wet-paper filtering, probabilistic layer splitting.", body_style)],
        [Paragraph("Machine Learning Decoder", body_style), Paragraph("PyTorch, TorchScript, CNN Model (3 channels)", body_style), Paragraph("3-channel patch extraction (32x32) and binary raised-dot state prediction (6-bit Braille configuration).", body_style)],
        [Paragraph("Translation & AI Layer", body_style), Paragraph("Custom Dictionaries, Google GenAI SDK (Gemini 2.5)", body_style), Paragraph("Multilingual decoding (AR, FR, EN, RU), language auto-detection, and contextual spelling refinement.", body_style)],
        [Paragraph("Speech Synthesis", body_style), Paragraph("Edge-TTS, Asyncio, Audio File streaming", body_style), Paragraph("Converts localized translation strings to high-fidelity audio streams for various dialects.", body_style)],
    ]
    
    t_arch = Table(arch_data, colWidths=[100, 150, 254])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EFF6FF")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(Spacer(1, 10))
    story.append(t_arch)
    
    story.append(PageBreak())
    
    # ------------------ PAGE 3: IMAGE PROCESSING PIPELINE ------------------
    story.append(Paragraph("3. The Image Processing Pipeline (CV Layer)", h1_style))
    story.append(Paragraph(
        "A critical innovation of this project is the non-destructive physical feature extraction pipeline. Instead of running "
        "pure end-to-end OCR (which fails on physical Braille due to camera angles, page curves, and double-sided printing), "
        "the backend runs a multi-stage mathematical computer vision pipeline in <b>OpenCV</b> and <b>Numba</b>:",
        body_style
    ))
    
    story.append(Paragraph("3.1. Perspective Warp & Curvature Rectification", h2_style))
    story.append(Paragraph(
        "Using 4 coordinates supplied interactively by the user, the backend performs a perspective warp "
        "(<code>cv2.getPerspectiveTransform</code> and <code>cv2.warpPerspective</code>) to extract the text sheet. "
        "This flattens page curl and guarantees a standardized orthographic coordinate workspace for grid alignment.",
        body_style
    ))
    
    story.append(Paragraph("3.2. Light Angle Calibration & Self-Translation Vectors", h2_style))
    story.append(Paragraph(
        "Since Braille dots are 3D raised spheres, their visibility depends on shadows. The UI allows inputting the lighting angle. "
        "The backend uses double adaptive thresholding (highlight-seeking and shadow-seeking) to find highlighting and shadow pixels. "
        "By template matching highlight and shadow layers against each other (using template matching self-correlation), "
        "the system finds the exact displacement vector representing the dot radius and lighting direction.",
        body_style
    ))
    
    story.append(Paragraph("3.3. Directional Wet-Paper (WB) Filtering", h2_style))
    story.append(Paragraph(
        "To filter out page noise and paper grain, a directional smoothing filter is implemented. It accumulates pixel differences "
        "along the primary horizontal, vertical, and diagonal directions. The accumulated 'wet-paper' gradient maps isolate raised "
        "dots while smoothing out flat areas and fibers.",
        body_style
    ))
    
    story.append(Paragraph("3.4. Probabilistic Layer Splitting (Recto/Verso Separation)", h2_style))
    story.append(Paragraph(
        "Double-sided Braille documents (Interpoint) print characters on both sides of the sheet. Sighted readers or standard scanners "
        "see 'bleed-through' indentations from the back page (Verso) mixed with front-page dots (Recto). "
        "The system separates them mathematically: under directional light, front-page raised dots cast shadows in one direction, "
        "while back-page depressions cast shadows in the opposite direction. By analyzing pixel pairs shifted along the estimated "
        "light vector, the backend builds two independent probability layers: one representing Recto dots, and the other Verso dots.",
        body_style
    ))
    
    story.append(Paragraph(
        "<b>Mathematical Formula:</b><br/>"
        "Let <i>C</i> be the raw grayscale contrast. The shadow shifts <i>v<sub>1</sub></i> and <i>v<sub>2</sub></i> "
        "represent recto and verso displacements. The probability of recto dot presence is computed as:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>P(Recto) = A / (A + B + &epsilon;)</i><br/>"
        "Where <i>A</i> is the shifted intensity map under <i>v<sub>1</sub></i>, and <i>B</i> is under <i>v<sub>2</sub></i>.",
        callout_style
    ))
    
    story.append(PageBreak())
    
    # ------------------ PAGE 4: GRID ALIGNMENT & DEEP LEARNING ------------------
    story.append(Paragraph("4. Grid Discovery, Modulo Voting & Belief Propagation", h1_style))
    story.append(Paragraph(
        "Once noise-free dot pixels are separated, they must be grouped into structural 3x2 cells. This is solved via "
        "spatial alignment and voting filters:",
        body_style
    ))
    
    story.append(Paragraph("4.1. Spatial Periodicity & Spacing Estimation", h2_style))
    story.append(Paragraph(
        "The system runs 2D template matching self-correlations on the binary dot masks to compute the structural rhythm of the page: "
        "the cell dot spacing (horizontal/vertical) and the inter-character/inter-line gaps.",
        body_style
    ))
    
    story.append(Paragraph("4.2. Markov-style Belief Propagation (Modulo Voting)", h2_style))
    story.append(Paragraph(
        "Because of paper warping or hand-written variations, absolute grids fail. Instead, a sparse KD-Tree graph of dot centers is built. "
        "A belief propagation solver (using SciPy CSR sparse matrix operations) runs iterative voting: neighboring dots vote on "
        "whether they belong to the same cell row (Top, Middle, Down) or column (Left, Right) based on modulo distance properties. "
        "Unsure dot assignments are updated iteratively based on the consensus of their neighbors. This algorithm achieves high tolerance "
        "against page rotation and skew.",
        body_style
    ))
    
    story.append(Paragraph("4.3. Grid Completion & Rescue", h2_style))
    story.append(Paragraph(
        "If some dots are missing due to low printing quality or scan wear, a grid density recovery step rescues them. "
        "It projects virtual cells horizontally and vertically and checks if loose pixels fit the pattern, 'rescuing' weak dots before decoding.",
        body_style
    ))

    story.append(Paragraph("5. Convolutional Neural Network (CNN) Classifier", h1_style))
    story.append(Paragraph(
        "For each rescued 3x2 cell bounding box, the backend extracts a 3-channel image patch of size 32x32. "
        "The channels are structured to maximize feature density:",
        body_style
    ))
    story.append(Paragraph(
        "<b>• Channel 1 (Original Grayscale):</b> Represents raw texture information.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>• Channel 2 (Separated Recto Intensity):</b> Focuses purely on extracted front-page dots.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>• Channel 3 (Verso/Recto Contrast Boundary):</b> Emphasizes edge transitions.",
        bullet_style
    ))
    
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "These patches are passed to a PyTorch CNN model (<code>DotPredictor</code>) consisting of three Conv2D layers, "
        "Batch Normalization, Max Pooling, Adaptive Average Pooling, and fully connected layers. The network predicts the binary "
        "state (0 or 1) of the 6 dot positions in the cell, outputting a 6-bit binary sequence representing the Braille character.",
        body_style
    ))
    
    # Model Architecture Code-block
    model_code = """
class DotPredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.fc_layers = nn.Sequential(
            nn.Linear(128, 64), nn.ReLU(),
            nn.Dropout(0.3), nn.Linear(64, 1), nn.Sigmoid()
        )
    """
    story.append(Paragraph(model_code.replace(" ", "&nbsp;").replace("\n", "<br/>"), code_style))
    story.append(PageBreak())
    
    # ------------------ PAGE 5: TRANSLATION & USER INTERFACE ------------------
    story.append(Paragraph("6. Multilingual Translation & LLM Refinement Layer", h1_style))
    story.append(Paragraph(
        "Once the CNN yields the Unicode Braille characters, the text is structured into reading lines by a custom "
        "<b>Universal Structural Assembler</b> (which preserves line feeds and spaces even on curved tables or margins). "
        "The text is then translated and processed through the following software stages:",
        body_style
    ))
    
    story.append(Paragraph("6.1. Rule-Based Dictionary Translations", h2_style))
    story.append(Paragraph(
        "The translation engine supports five localized lookup tables based on standard international usage:",
        body_style
    ))
    story.append(Paragraph("• <b>Arabic:</b> World Braille Usage standard (translating ligatures, harakat diacritics, and numeric indicator modes).", bullet_style))
    story.append(Paragraph("• <b>French:</b> Braille Français Uniformisé (BFU) standard (handling accented characters, capital indicator states).", bullet_style))
    story.append(Paragraph("• <b>English Grade 1:</b> UEB literal letter-for-letter mapping.", bullet_style))
    story.append(Paragraph("• <b>English Grade 2:</b> Unified English Braille contraction logic (handling whole-word and part-word rules).", bullet_style))
    story.append(Paragraph("• <b>Russian:</b> GOST R 58511-2019 Cyrillic mapping.", bullet_style))
    
    story.append(Paragraph("6.2. Auto-Language Detection", h2_style))
    story.append(Paragraph(
        "A highly powerful user option is <i>Auto-Detect</i>. The backend transcribes the Braille Unicode using all 5 translation tables "
        "simultaneously. It then compiles the 5 raw candidates into a single prompt sent to <b>Gemini 2.5 Flash Lite</b>. "
        "The model analyzes semantic coherence and returns a structured JSON package containing the identified language "
        "and a corrected translation, avoiding the need for manual selection.",
        body_style
    ))
    
    story.append(Paragraph("6.3. Gemini AI Spelling and Grammar Correction", h2_style))
    story.append(Paragraph(
        "Because Braille images can contain worn paper or dust, small OCR typos can occur. The system leverages the "
        "Google GenAI SDK. If the selected language is not 'raw', the translation is sent to Gemini to fix punctuation, "
        "spacing, and formatting. The prompt is also tailored to identify fill-in-the-gap educational sheets, "
        "automatically replacing blank exam slots with clean dashes (<code>-----</code>).",
        body_style
    ))
    
    story.append(Paragraph("6.4. Text-To-Speech (TTS)", h2_style))
    story.append(Paragraph(
        "The translation result is accessible to visually impaired or learning users through an integrated TTS engine powered by "
        "<code>edge-tts</code>. The backend queries available Microsoft Neural voices, categorizes them by language/dialect, "
        "and streams synthesized audio back to the frontend browser dynamically.",
        body_style
    ))

    story.append(Paragraph("7. Streaming & Interactive Client Dashboard", h1_style))
    story.append(Paragraph(
        "To ensure a responsive user experience despite the latency of deep learning models and LLM API calls, the frontend and "
        "backend communicate via <b>Server-Sent Events (SSE)</b>. When processing an image, the FastAPI server yields chunks progressively:",
        body_style
    ))
    story.append(Paragraph("<b>1. Stage 'overlay':</b> Streams the cropped page image with annotated character boxes immediately after grid completion.", bullet_style))
    story.append(Paragraph("<b>2. Stage 'braille':</b> Emits the transcribed raw Braille Unicode symbols.", bullet_style))
    story.append(Paragraph("<b>3. Stage 'detected_language':</b> (If in Auto-Detect mode) Identifies and emits the detected language key.", bullet_style))
    story.append(Paragraph("<b>4. Stage 'translation':</b> Emits the fast dictionary-translated text string.", bullet_style))
    story.append(Paragraph("<b>5. Stage 'gemini':</b> Emits the final context-corrected translation once the Gemini response arrives.", bullet_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "This progressive stream prevents the browser UI from locking up and keeps the user informed of the exact processing state.",
        body_style
    ))
    
    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print("✅ PDF document generated successfully.")

if __name__ == "__main__":
    build_pdf()
