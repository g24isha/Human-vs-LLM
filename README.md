
# Human-vs-AI

Overview

This repository contains Python scripts developed for the Human vs. AI Research Idea Creation Project conducted with the Social and Language Technologies (SALT) Lab at Stanford University, a study comparing the quality of research ideas generated by humans versus those generated by large language models (LLMs), such as ChatGPT. The scripts automate the data collection, evaluation, and analysis processes for the project, leveraging Google Drive, Google Forms, and Google Sheets APIs to streamline the creation of evaluation forms and the collection of reviewer responses.

Features

	•	Automated Google Form Generation: Converts research ideas from .docx files into text format and generates customized Google Forms for each idea for evaluation purposes.
	•	Real-time Data Collection and Management: Uses Google Sheets to store and update reviewer responses in real-time, including ratings on novelty, feasibility, expected effectiveness, excitement, and overall score.
	•	Rate-Limit Handling with Exponential Backoff: Implements an exponential backoff algorithm to efficiently manage API rate limits during high-volume operations, ensuring smooth data collection and analysis.
	•	Statistical Analysis Preparation: Prepares data for advanced statistical analysis, such as z-score normalization and t-tests, to evaluate differences in the quality of ideas generated by humans and AI.

