const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  ImageRun, PageBreak,
} = require("docx");

const W = 9026;            // A4 usable width in DXA (1" margins)
const GREY = "F2F2F2";
const CURRENT_BG = "FDF0EF";
const NEW_BG = "EDF5EC";

const p = (text, opts = {}) =>
  new Paragraph({
    spacing: { after: opts.after ?? 140, line: opts.line ?? 276 },
    alignment: opts.align,
    indent: opts.indent,
    children: [new TextRun({
      text,
      italics: opts.italics,
      bold: opts.bold,
      size: opts.size ?? 22,
      color: opts.color,
      font: opts.font,
    })],
  });

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 320, after: 180 },
  children: [new TextRun({ text, bold: true, size: 30, color: "1A1A1A" })],
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 300, after: 120 },
  children: [new TextRun({ text, bold: true, size: 24, color: "1A1A1A" })],
});

// A labelled, shaded block of quoted text.
const block = (label, text, bg) => new Table({
  columnWidths: [W],
  width: { size: W, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" },
    bottom: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" },
    left: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" },
    right: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC" },
    insideHorizontal: { style: BorderStyle.NONE },
    insideVertical: { style: BorderStyle.NONE },
  },
  rows: [new TableRow({
    children: [new TableCell({
      width: { size: W, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: bg },
      margins: { top: 120, bottom: 120, left: 160, right: 160 },
      children: [
        new Paragraph({
          spacing: { after: 60 },
          children: [new TextRun({ text: label, bold: true, size: 18,
                                   color: "555555", allCaps: true })],
        }),
        new Paragraph({
          spacing: { after: 0, line: 276 },
          children: [new TextRun({ text, size: 22 })],
        }),
      ],
    })],
  })],
});

const spacer = () => new Paragraph({ spacing: { after: 160 }, children: [] });

const figure = (file, caption, width, height) => [
  new Paragraph({
    spacing: { before: 200, after: 80 },
    alignment: AlignmentType.CENTER,
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(file),
      transformation: { width, height },
    })],
  }),
  new Paragraph({
    spacing: { after: 240 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: caption, size: 20, bold: true })],
  }),
];

// -------------------------------------------------------------------------
const summaryRows = [
  ["Abstract", "Reword the deployment sentence", "Required"],
  ["Chapter One, §1.2 (Method, bullet 5)", "Reword the deployment bullet", "Required"],
  ["Chapter One, §1.3 (Aim and Objectives)", "No change — already framework-neutral", "None"],
  ["Chapter Two (classifier/deployment mention)", "Swap the framework names", "Required"],
  ["Chapter Two (research gap, Owoade discussion)", "Swap the framework names", "Required"],
  ["Chapter Two, §2.1.2 (Technologies)", "Add Node.js, Express and JSON as technologies", "Check & add"],
  ["Chapter Three, §3.1 (Deployment Phase)", "Reword and state the rationale for the split", "Required"],
  ["Chapter Three, §3.2.2 (proposed system)", "Reword the application sentence", "Required"],
  ["Chapter Three, §3.2.2 (three-layer paragraph)", "Add a paragraph naming each layer's technology", "Recommended"],
  ["Chapter Three, §3.3.3 (Sequence diagram text)", "Factual correction — the service does not write to the database", "Critical"],
  ["Figure 3.3 (Sequence diagram)", "Redraw — replacement supplied below", "Critical"],
  ["Figure 3.5 (Architecture diagram)", "New figure — supplied below", "Recommended"],
  ["Figures 3.1, 3.2 (Use case, Activity)", "No change — they describe behaviour, not deployment", "None"],
  ["Figure 3.4 (Class diagram)", "No change — optionally note where each class resides", "Optional"],
];

const summaryTable = new Table({
  columnWidths: [3100, 4276, 1650],
  width: { size: W, type: WidthType.DXA },
  rows: [
    new TableRow({
      tableHeader: true,
      children: ["Location", "Change required", "Priority"].map((t, i) =>
        new TableCell({
          width: { size: [3100, 4276, 1650][i], type: WidthType.DXA },
          shading: { type: ShadingType.CLEAR, fill: "DDE6EE" },
          margins: { top: 90, bottom: 90, left: 120, right: 120 },
          children: [new Paragraph({
            spacing: { after: 0 },
            children: [new TextRun({ text: t, bold: true, size: 20 })],
          })],
        })),
    }),
    ...summaryRows.map((row) => new TableRow({
      children: row.map((t, i) => new TableCell({
        width: { size: [3100, 4276, 1650][i], type: WidthType.DXA },
        margins: { top: 90, bottom: 90, left: 120, right: 120 },
        children: [new Paragraph({
          spacing: { after: 0 },
          children: [new TextRun({
            text: t,
            size: 19,
            bold: i === 2 && (t === "Critical"),
            color: i === 2 && t === "None" ? "777777" : "000000",
          })],
        })],
      })),
    })),
  ],
});

// -------------------------------------------------------------------------
const children = [
  new Paragraph({
    spacing: { after: 60 },
    children: [new TextRun({
      text: "Revisions Required to Chapters One, Two and Three",
      bold: true, size: 34,
    })],
  }),
  new Paragraph({
    spacing: { after: 40 },
    children: [new TextRun({
      text: "An AI-Based Mental Health Monitoring and Sentiment Analysis System",
      size: 22, color: "555555",
    })],
  }),
  new Paragraph({
    spacing: { after: 300 },
    children: [new TextRun({
      text: "Arising from the adoption of a two-process architecture: a Flask inference service consumed by a Node.js (Express) presentation layer.",
      size: 20, italics: true, color: "555555",
    })],
  }),

  p("The three written chapters commit the project to a Flask or Streamlit deployment layer. Moving the presentation layer to Node.js requires those commitments to be updated. Most of the changes are a matter of naming the correct frameworks. One is not: the description accompanying the sequence diagram in §3.3.3 states that the classification service writes the submission record to the database, which is no longer true and would read as an inconsistency between the design chapter and the implementation chapter."),

  p("The replacement wording below is drafted to drop directly into the document. Where a change is optional it is marked as such."),

  h1("1. Summary of changes"),
  summaryTable,
  spacer(),

  new Paragraph({ children: [new PageBreak()] }),

  h1("2. Replacement wording"),

  h2("2.1  Abstract"),
  block("Current text",
    "The top-performing model is then served behind a web interface using Flask/Streamlit to take input of text and provide a classification result, all of which are saved to an SQLite database.",
    CURRENT_BG),
  spacer(),
  block("Replacement",
    "The top-performing model is then served behind a Flask inference service, which a Node.js (Express) web dashboard consumes in order to take text input from the user and present a classification result, with each submission saved to an SQLite database.",
    NEW_BG),

  h2("2.2  Chapter One, §1.2 — Method, fifth bullet"),
  block("Current text",
    "Deploy the best-performing model behind a simple web dashboard (Flask and/or Streamlit) that accepts free-text input and returns a classification with a simple explanation.",
    CURRENT_BG),
  spacer(),
  block("Replacement",
    "Deploy the best-performing model behind a Flask inference service, consumed by a Node.js (Express) web dashboard that accepts free-text input and returns a classification with a simple explanation.",
    NEW_BG),

  h2("2.3  Chapter One, §1.3 — Aim and Objectives"),
  p("No change is required. The fifth objective reads “To deploy the best-performing model in a web-based dashboard for real-time text classification”, which names no framework and remains exactly true of the system as built. Leaving it untouched is preferable to editing it, since an objective that survives an architectural change unchanged is evidence that it was well stated."),

  h2("2.4  Chapter Two — deployment mention following the classifier descriptions"),
  block("Current text",
    "… prior to deployment of this classifier behind the Flask/Streamlit web dashboard described in Chapter 3.",
    CURRENT_BG),
  spacer(),
  block("Replacement",
    "… prior to deployment of this classifier behind the Flask inference service and Node.js web dashboard described in Chapter 3.",
    NEW_BG),

  h2("2.5  Chapter Two — research gap, following the discussion of Owoade (2025)"),
  block("Current text",
    "… nor did either yield a usable and user-friendly interface (this work’s deployment layer in Flask/Streamlit is designed to fill this gap).",
    CURRENT_BG),
  spacer(),
  block("Replacement",
    "… nor did either yield a usable and user-friendly interface (this work’s deployment layer — a Flask inference service behind a Node.js web dashboard — is designed to fill this gap).",
    NEW_BG),

  h2("2.6  Chapter Two, §2.1.2 — Technologies"),
  p("Check whether this subsection names Flask or Streamlit among the technologies underpinning the study. If it does, replace that entry with the paragraph below; if it does not, add the paragraph anyway, since the presentation-layer technology now warrants introduction alongside Python, NLP and machine learning."),
  spacer(),
  block("Suggested addition",
    "Node.js and Express: Node.js is a runtime that executes JavaScript outside the browser, and Express is a minimal web framework built upon it. Together they provide the presentation layer of the proposed system — routing, page rendering, session handling and persistence — while the classification model itself remains in Python. The two layers communicate over HTTP using JSON (JavaScript Object Notation), a lightweight, language-independent data-interchange format. It is this language independence that allows a JavaScript presentation layer to make use of a machine-learning model that exists only as a Python object.",
    NEW_BG),

  new Paragraph({ children: [new PageBreak()] }),

  h2("2.7  Chapter Three, §3.1 — CRISP-DM, Deployment Phase"),
  block("Current text",
    "Deployment Phase: The best performing model (along with the fitted TF-IDF vectorizer) will be deployed using a Flask/Streamlit web interface, where the user will be able to enter free text, and get a classification result back.",
    CURRENT_BG),
  spacer(),
  block("Replacement",
    "Deployment Phase: The best performing model, together with the fitted TF-IDF vectorizer, is deployed as a Flask inference service which exposes the classifier over HTTP as a JSON interface. A Node.js (Express) web dashboard consumes that interface, allowing the user to enter free text and receive a classification result. The separation is deliberate rather than incidental: a scikit-learn model is a Python object and can only be loaded by a Python process, whereas the presentation layer — rendering pages, managing sessions and storing submissions — requires no Python at all. Each layer is therefore implemented in the language best suited to it.",
    NEW_BG),

  h2("2.8  Chapter Three, §3.2.2 — Analysis of the Proposed System"),
  block("Current text",
    "After finding the best performing model, it is incorporated into an application using Flask or Streamlit that allows a user to get a classification result using a simple Web application, and store the submissions on an SQLite database.",
    CURRENT_BG),
  spacer(),
  block("Replacement",
    "After finding the best performing model, it is incorporated into a Flask inference service that exposes classification over HTTP. A Node.js (Express) web application consumes this service, allowing a user to submit free text, receive a classification result, and have each submission stored in an SQLite database.",
    NEW_BG),

  h2("2.9  Chapter Three, §3.2.2 — paragraph to add after the three-layer description"),
  p("The existing three-layer description is technology-neutral and remains correct as written, so this addition is not strictly required. It is recommended because it makes the architecture concrete and shows that the implemented system follows the documented design rather than merely resembling it."),
  spacer(),
  block("Paragraph to add",
    "In implementation these three layers are separated across two processes. The presentation layer is a Node.js application built with the Express framework, which renders the interface, issues a session token and stores submissions. The middle layer is a Flask service written in Python, which holds the text pre-processing pipeline, the fitted TF-IDF vectorizer and the trained classifier. The data layer comprises the SQLite database of submissions together with the persisted model artefacts. The two processes communicate over HTTP using JSON. All text pre-processing is performed within the middle layer, so that text submitted by a user at run time is transformed by exactly the same procedure as the text used to train the classifier; performing any cleaning in the presentation layer would break that correspondence and degrade every prediction. The inference service holds no state of its own, session tokens and submission records being the responsibility of the presentation layer. Figure 3.5 illustrates this arrangement.",
    NEW_BG),

  new Paragraph({ children: [new PageBreak()] }),

  h2("2.10  Chapter Three, §3.3.3 — The Sequence Diagram"),
  p("This is the one change that is a correction of fact rather than of naming. The current text states that the classification service stores the record in the database. In the implemented system the service is stateless; the dashboard writes the record, because it is the dashboard that owns the session token the record is filed against. Left unamended, Chapter Three would contradict Chapter Four.",
    { }),
  spacer(),
  block("Current text",
    "… the sequence diagram captures the interaction flow when a user submits text for classification: the User sends input through the Dashboard, which invokes the Classification Service, the service then generates a feature vector and requests a prediction from the trained Model; the Model returns a label and confidence score; the service stores the record in the SQLite Database and returns the result to the interface for display.",
    CURRENT_BG),
  spacer(),
  block("Replacement",
    "Sequence diagrams illustrate the dynamic interaction between system actors and its components, focusing on the order of message exchanges. In the proposed system, the sequence diagram captures the interaction flow when a user submits text for classification. The User enters a text entry through the Dashboard, which forwards the raw, uncleaned text to the Classification Service over HTTP. The service pre-processes the text, converts it into a TF-IDF feature vector and requests a prediction from the trained Model; the Model returns a predicted label together with a confidence score, which the service returns to the Dashboard as a JSON response. The Dashboard then stores the record in the SQLite Database against the user’s session token, and displays the result, accompanied by a referral prompt where the predicted class is not Normal. The Classification Service itself retains no record of the submission.",
    NEW_BG),

  new Paragraph({ children: [new PageBreak()] }),

  h1("3. Figures"),

  h2("3.1  Figure 3.3 — Sequence Diagram (replacement)"),
  p("This replaces the existing Figure 3.3. The database now sits beyond the Dashboard rather than beyond the Classification Service, and the pre-processing step is shown explicitly as occurring inside the service."),
  ...figure("results/figures/fig_3_3_sequence_diagram_revised.png",
    "Figure 3.3: Sequence Diagram", 452, 281),

  h2("3.2  Figure 3.5 — System Architecture (new)"),
  p("A new figure, to be placed at the end of §3.2.2 immediately after the paragraph given in 2.9 above. It gives the reader a single picture of the three layers, the two processes and what passes between them."),
  ...figure("results/figures/fig_3_5_system_architecture.png",
    "Figure 3.5: Deployment Architecture of the Proposed System", 430, 319),

  h2("3.3  Figures requiring no change"),
  p("Figure 3.1 (Use Case) and Figure 3.2 (Activity) describe what the user does and the order in which the system responds. Neither depends on how the system is deployed, so both stand unaltered."),
  p("Figure 3.4 (Class Diagram) also stands. The Submission, Preprocessor and Classifier classes and their dependencies are unchanged. You may optionally note in the accompanying text that Preprocessor and Classifier reside within the inference service, while Submission is materialised by the presentation layer when it writes to the database."),

  h1("4. Answering the examiner"),
  p("Expect to be asked why the system uses two languages when one would do. The answer is architectural rather than preferential, and is worth rehearsing:"),
  p("A trained scikit-learn model is a Python object. It is serialised as a Python object graph and cannot be loaded by any other runtime, so the classifier must be served from a Python process — that is not a choice. The presentation layer, however, has no need of Python whatsoever: it renders pages, manages a session and writes rows to a database. Separating the two allows each layer to be implemented in the language best suited to it, and maps the implementation directly onto the three-layer architecture set out in §3.2.2, in which the presentation and middle layers are distinct concerns. A single-process implementation would collapse those two layers into one, which is simpler to operate but less faithful to the documented design.",
    { }),
  p("A second question is likely to follow: why does the presentation layer send raw text rather than cleaning it first? Because the classifier was trained on features produced by one specific pre-processing pipeline. Any cleaning performed elsewhere — even something as innocuous as trimming or lowercasing — risks diverging from that pipeline, and the resulting predictions would degrade without raising any error. Confining pre-processing to the service guarantees that text classified at run time is transformed exactly as the training corpus was."),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("Chapter_1-3_Revisions.docx", buf);
  console.log("written Chapter_1-3_Revisions.docx");
});
