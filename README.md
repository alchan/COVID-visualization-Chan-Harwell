# COVID-visualization-Chan-Harwell

__Using the Program:__
1. Install plotly and dash using pip or a similar package manager
2. Run the program using Python 3
3. The program dynamically pulls the latest data from the NY Times GitHub page at launch
4. The initial program startup will take a number of minutes to create an assets folder with cached choropleth images.
      Future program executions in the same directory as the populated assets folder will be expedient.


__About:__
The COVID-19 pandemic has dramatically reshaped social habits, financial markets, and medical technology on a global scale. 
Presenting such a risk to public health has made tracking COVID-19 cases and deaths a top priority for major institutions including 
the Center for Disease Control and Prevention (CDC), the World Health Organization (WHO), and the New York Times.
These bodies publish extensive open-source statistics available for public use. 

Clinical research has shown however that data is more impactful when it is presented not just textually, but graphically. 
Virologists and other medical professionals need information that is both accurate and easy to digest. 
This research thus focuses on plotting COVID-19 cases/deaths by county on a choropleth map of the United States. 
The application queries open-source data from the New York Times before generating a choropleth map that users can traverse by date.
An animation is also included in order to track general trends on a larger timescale. 

This research has culminated in a powerful utility that will allow researchers to track the spread of COVID-19 more efficiently in 
order to aid in crafting more effective health policies.
