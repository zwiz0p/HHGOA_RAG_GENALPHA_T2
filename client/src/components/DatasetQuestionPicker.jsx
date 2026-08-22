import React, { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp, Sparkles, Languages, Check, Search, ArrowUpRight } from "lucide-react";
import { Glass } from "@samasante/liquid-glass";

const DATASET_QUESTIONS = {
  english: [
    {
      category: "History & Defense",
      query: "Who directed the Los Alamos Laboratory during the Manhattan Project?",
      desc: "Robert Oppenheimer & bomb design",
    },
    {
      category: "History & Defense",
      query: "what was the immediate impact of the success of the manhattan project?",
      desc: "Scientific communication & WWII impact",
    },
    {
      category: "Databases & Tech",
      query: "how to use sysdate in sql",
      desc: "Oracle PL/SQL date & time retrieval",
    },
    {
      category: "Law & Justice",
      query: "what does laches mean in legal terms",
      desc: "Laches doctrine vs statute of limitations",
    },
    {
      category: "Government & Benefits",
      query: "different types of social security disability",
      desc: "SSD benefits & beneficiary qualifications",
    },
    {
      category: "Finance & Taxation",
      query: "can u claim cpa fees paid to a state audit on the itemized deduction form",
      desc: "Miscellaneous itemized deduction rules",
    },
    {
      category: "Education & Life",
      query: "what do graduate students wear to class",
      desc: "Grad student style: competitive casual",
    },
    {
      category: "Cinema & Culture",
      query: "coal miner's daughter cast",
      desc: "Loretta Lynn biopic starring Sissy Spacek",
    },
    {
      category: "Culture & Society",
      query: "what does the american flag sticker on cars mean",
      desc: "Automotive decals and expressions of pride",
    },
    {
      category: "Technology & Media",
      query: "what is dvr service",
      desc: "Digital video recording & live television",
    },
  ],
  hindi: [
    {
      category: "इतिहास एवं रक्षा",
      query: "मैनहट्टन परियोजना कब शुरू हुई थी?",
      desc: "जून 1942 में अमेरिकी सेना के अभियंताओं द्वारा शुरुआत",
    },
    {
      category: "इतिहास एवं रक्षा",
      query: "मैनहट्टन परियोजना की सफलता का तुरंत क्या प्रभाव पड़ा?",
      desc: "वैज्ञानिक संचार और द्वितीय विश्व युद्ध पर प्रभाव",
    },
    {
      category: "डेटाबेस एवं तकनीक",
      query: "सिसडेट का उपयोग कैसे करें?",
      desc: "डेटाबेस में वर्तमान तिथि और समय निर्धारित करना",
    },
    {
      category: "कानून एवं न्याय",
      query: "कानूनी शब्दावली में 'लाच' का क्या अर्थ है",
      desc: "लाच सिद्धांत और कानूनी समय सीमा",
    },
    {
      category: "सरकारी योजनाएं",
      query: "विभिन्न प्रकार की सामाजिक सुरक्षा विकलांगता",
      desc: "सामाजिक सुरक्षा विकलांगता लाभ (एस.एस.डी.) और पात्रता",
    },
    {
      category: "वित्त एवं कर",
      query: "क्या आप विस्तृत कटौती प्रपत्र पर राज्य के लिए भुगतान किए गए सी.पी.ए. शुल्क का दावा कर सकते हैं?",
      desc: "बिक्री कर एवं विविध कटौती दावे",
    },
    {
      category: "शिक्षा एवं जीवन",
      query: "स्नातक छात्र कक्षा में क्या पहनते हैं",
      desc: "स्नातक छात्रों की प्रतिस्पर्धी अनौपचारिक पोशाक",
    },
    {
      category: "सिनेमा एवं संस्कृति",
      query: "कोयला खनिक की बेटी कास्ट",
      desc: "लोरेटा लिन की जीवनी फिल्म (सिसी स्पेसेक)",
    },
    {
      category: "संस्कृति एवं समाज",
      query: "कारों पर अमेरिकी ध्वज के स्टिकर का क्या अर्थ है?",
      desc: "ऑटो और कारों पर राष्ट्रीय अभिव्यक्ति",
    },
    {
      category: "शब्दावली एवं भाषा",
      query: "लिफ्ट का मतलब है",
      desc: "एलिवेटर संज्ञा के परिभाषा और अर्थ",
    },
  ],
};

export default function DatasetQuestionPicker({ onSelectPrompt, disabled }) {
  const [isOpen, setIsOpen] = useState(false);
  const [lang, setLang] = useState("english"); // 'english' | 'hindi'
  const [searchTerm, setSearchTerm] = useState("");

  const questions = DATASET_QUESTIONS[lang] || [];
  const filtered = questions.filter(
    (q) =>
      q.query.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.desc.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  function handlePick(query) {
    onSelectPrompt(query);
    setIsOpen(false);
  }

  return (
    <div style={{ position: "relative", display: "inline-block", userSelect: "none" }}>
      {/* Dropdown Trigger Button */}
      <Glass
        optics={{
          depth: 0.8,
          dispersion: 0.35,
          strength: 0.65,
          frost: 14,
          brightness: 0.12,
          specular: 1.6,
          sheen: 1.0,
          glow: 0.45,
          curvature: 0.45,
          bend: 0.28,
          bendWidth: 0.14,
        }}
        radius={999}
        style={{ borderRadius: "999px" }}
      >
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className="liquid-glass-btn font-accent"
          style={{
            padding: "7px 18px",
            fontSize: "13.5px",
            fontWeight: 700,
            gap: "7px",
            color: "var(--ink)",
            borderRadius: "999px",
            backgroundColor: isOpen ? "rgba(255, 255, 255, 0.85)" : "rgba(255, 255, 255, 0.55)",
            border: isOpen ? "1.5px solid var(--sun)" : "1.5px solid rgba(255, 255, 255, 0.80)",
            boxShadow: isOpen ? "0 0 20px rgba(245, 158, 11, 0.45)" : undefined,
          }}
        >
          <BookOpen size={14} color="var(--sun-dark)" />
          <span>Ask from Dataset Corpus</span>
          <span
            style={{
              fontSize: "11px",
              padding: "2px 7px",
              borderRadius: "999px",
              backgroundColor: lang === "hindi" ? "rgba(254, 243, 199, 0.85)" : "rgba(220, 252, 231, 0.85)",
              color: lang === "hindi" ? "#B45309" : "#15803D",
              fontWeight: 800,
            }}
          >
            {lang === "hindi" ? "हिन्दी (HI)" : "English (EN)"}
          </span>
          {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </Glass>

      {/* Expandable Liquid Glass Popover Menu */}
      {isOpen && (
        <>
          {/* Backdrop Click Dismiss */}
          <div
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 998,
            }}
            onClick={() => setIsOpen(false)}
          />

          <div
            className="liquid-glass-card"
            style={{
              position: "absolute",
              bottom: "calc(100% + 12px)",
              left: "50%",
              transform: "translateX(-50%)",
              width: "min(92vw, 560px)",
              maxHeight: "440px",
              display: "flex",
              flexDirection: "column",
              zIndex: 999,
              padding: "18px 20px",
              backgroundColor: "rgba(255, 255, 255, 0.65)",
              backdropFilter: "blur(40px) saturate(210%)",
              WebkitBackdropFilter: "blur(40px) saturate(210%)",
              boxShadow: "0 28px 70px -10px rgba(15, 23, 42, 0.28), 0 10px 25px rgba(0,0,0,0.10)",
              border: "1.5px solid rgba(255, 255, 255, 0.85)",
              textAlign: "left",
            }}
          >
            {/* Header: Title & Language Switcher Tabs */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "8px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Sparkles size={16} color="var(--sun)" />
                <span className="font-sans" style={{ fontSize: "15px", fontWeight: 800, color: "var(--ink)" }}>
                  Verified Dataset Questions
                </span>
              </div>

              {/* Language Switcher Pills */}
              <div
                style={{
                  display: "inline-flex",
                  padding: "3px",
                  borderRadius: "999px",
                  backgroundColor: "rgba(0, 0, 0, 0.06)",
                  border: "1px solid rgba(0, 0, 0, 0.08)",
                }}
              >
                <button
                  type="button"
                  onClick={() => setLang("english")}
                  className="font-accent"
                  style={{
                    padding: "4px 12px",
                    borderRadius: "999px",
                    fontSize: "12px",
                    fontWeight: 800,
                    border: "none",
                    cursor: "pointer",
                    backgroundColor: lang === "english" ? "#FFFFFF" : "transparent",
                    color: lang === "english" ? "var(--ink)" : "var(--ink-soft)",
                    boxShadow: lang === "english" ? "0 2px 8px rgba(0,0,0,0.12)" : "none",
                    transition: "all 0.15s ease",
                  }}
                >
                  English (EN)
                </button>
                <button
                  type="button"
                  onClick={() => setLang("hindi")}
                  className="font-accent"
                  style={{
                    padding: "4px 12px",
                    borderRadius: "999px",
                    fontSize: "12px",
                    fontWeight: 800,
                    border: "none",
                    cursor: "pointer",
                    backgroundColor: lang === "hindi" ? "#FFFFFF" : "transparent",
                    color: lang === "hindi" ? "var(--ink)" : "var(--ink-soft)",
                    boxShadow: lang === "hindi" ? "0 2px 8px rgba(0,0,0,0.12)" : "none",
                    transition: "all 0.15s ease",
                  }}
                >
                  हिन्दी (HI)
                </button>
              </div>
            </div>

            {/* Quick Search Filter Bar */}
            <div
              className="liquid-glass-subtle"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "6px 12px",
                marginBottom: "12px",
              }}
            >
              <Search size={14} color="var(--ink-soft)" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={lang === "hindi" ? "विषय या प्रश्न खोजें..." : "Filter questions by topic..."}
                className="font-sans"
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  fontSize: "13px",
                  color: "var(--ink)",
                  fontWeight: 600,
                }}
              />
              {searchTerm && (
                <button
                  type="button"
                  onClick={() => setSearchTerm("")}
                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: "11px", color: "var(--ink-soft)", fontWeight: 700 }}
                >
                  Clear
                </button>
              )}
            </div>

            {/* Questions Scrollable List */}
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                paddingRight: "4px",
              }}
            >
              {filtered.length > 0 ? (
                filtered.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => handlePick(item.query)}
                    className="liquid-glass-subtle"
                    style={{
                      padding: "10px 14px",
                      cursor: "pointer",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "10px",
                      transition: "transform 0.15s ease, background 0.15s ease",
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.transform = "translateX(3px)";
                      e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 1)";
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.transform = "translateX(0)";
                      e.currentTarget.style.backgroundColor = "rgba(255, 255, 255, 0.90)";
                    }}
                  >
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px", minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span
                          className="font-accent"
                          style={{
                            fontSize: "10.5px",
                            fontWeight: 800,
                            color: "var(--sun-dark)",
                            textTransform: "uppercase",
                            letterSpacing: "0.4px",
                          }}
                        >
                          {item.category}
                        </span>
                      </div>
                      <span
                        className={lang === "hindi" ? "font-hindi" : "font-sans"}
                        style={{
                          fontSize: "13.5px",
                          fontWeight: 700,
                          color: "var(--ink)",
                          lineHeight: 1.35,
                        }}
                      >
                        {item.query}
                      </span>
                      <span
                        className={lang === "hindi" ? "font-hindi" : "font-accent"}
                        style={{
                          fontSize: "12px",
                          color: "var(--ink-soft)",
                          fontWeight: 600,
                        }}
                      >
                        {item.desc}
                      </span>
                    </div>

                    <div
                      style={{
                        flexShrink: 0,
                        width: "28px",
                        height: "28px",
                        borderRadius: "50%",
                        backgroundColor: "rgba(220, 252, 231, 0.95)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        border: "1px solid rgba(34, 197, 94, 0.3)",
                      }}
                    >
                      <ArrowUpRight size={14} color="#15803D" strokeWidth={2.5} />
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ textAlign: "center", padding: "24px 0", color: "var(--ink-soft)", fontSize: "13px" }}>
                  No matching questions found in this category.
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
