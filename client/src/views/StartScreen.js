import React from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/layout/Home.js";
import "../App.css";

function StartScreen() {
  const navigate = useNavigate();

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(
        "http://127.0.0.1:5000/chat_processing/process_chatlog",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      alert("File uploaded successfully");
      e.target.value = null;
    } catch (error) {
      console.log(error);
      alert("Error processing file");
      e.target.value = null;
    }
  };

  return (
    <>
      <div>
        <Header />
      </div>
      <div className="start-container">
        {/* Welcoming Section */}
        <section className="welcome-section">
          <h1>Welcome to DSA Character Analyzer</h1>
          <p>
            Discover the depths of your characters in the world of Das Schwarze
            Auge.
          </p>
          <button
            className="button"
            onClick={() => document.getElementById("file-input").click()}
          >
            Upload a Chatlog
          </button>
          <input
            id="file-input"
            type="file"
            onChange={handleFileChange}
            style={{ display: "none" }}
          />
        </section>

        {/* Purpose and Features Section */}
        <section className="purpose-section">
          <h2>What We Offer</h2>
          <p>
            Explore talent usage, track character development, and dive into the
            detailed analysis of your DSA adventures.
          </p>
        </section>

        {/* DSA Background Section */}
        <section className="background-section">
          <h2>About Das Schwarze Auge</h2>
          <p>
            DSA is a classic fantasy role-playing game, rich with lore and
            adventure. Dive into a world of magic, mystery, and intrigue.
          </p>
        </section>

        {/* Character Highlights Section */}
        <section className="character-highlights">
          <h2>Character Highlights</h2>
          <p>
            Explore the talents of your characters and how they have developed
            over time.
          </p>
          <button className="button" onClick={() => navigate("/characters")}>
            Manage Characters
          </button>
          <button
            className="button"
            onClick={() => navigate("/talents/<character_name>")}
          >
            Explore Characters
          </button>
        </section>

        {/* Talent Highlights Section */}
        <section className="character-highlights">
          <h2>Experience Points Academy</h2>
          <p>
            Explore how to best spend your experience points to develop your
            character.
          </p>
          <button
            className="button"
            onClick={() => navigate("/traits-for-selected-talents")}
          >
            Explorer
          </button>
        </section>
      </div>
    </>
  );
}

export default StartScreen;
