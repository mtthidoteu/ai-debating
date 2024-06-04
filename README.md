# AI Debating
This is a project I did that uses the OpenAI API to run debates betweeb two AI models. Instead of use the context window however, we used a form of homemade RAG. The idea is for previous debates to be used to improve on the current answer without resorting to context. Instead, we use a variety of metrics to determin the quality of the argument which is fed back to the model.

## Video Demonstration
[Video Example](https://odysee.com/ai-debating-example:7ba02235c499304e5a3826ccf33c458bd6bfaede)

## Viewing Metrics
The "main" page is the page showing the current metrics and a few graphgs that were used in the report



## Own Running Instructions

50 Debates have already been run and are including in the existing database file. To run more debates, follow the instructions below.


1. Add OpenAI API to key to .env
### Run a Single debate
2. Click the Debate screen and enter a question

### Run debates from questions.csv
2. Specifiy Number of Runs to Make in .env file (include those that must already be run) if you want to run automatically, currently there are 50 debates in the database
3. Click the 'Auto Run'

