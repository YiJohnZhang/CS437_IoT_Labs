
1. A written report is DIRECTLY required for this lab.
2. Grading scale:
	1. **Build the Cloud**: The students should leverage IoT components including a Hub, GreenGrass, IoT Core, IoT Analytics, IoT Device Defender to construct an infrastructure.
		- If the students have set up, configured and emulated the device group and rules, and are able to demonstrate communication between Greengrass devices and core they get 30 points
	2. **Data Inference**: The students must utilize GreenGrass components or Lambda functions to analyze emission levels of vehicles and return the results back to the device. **Please describe your design approach for returning the results**.
		- If the students are able to correctly implement the message processing to analyze the CO2 level, create the GreenGrass components or Lambda functions with appropriate rules, publish the results back to the subscriber device and simulate the entire process they get 30 points
	3. **Use AWS Firehose to visualize the Data**: For this section, students must create a SQL database and then visualize the data using the Jupyter notebook provided with AWS Sagemaker. Students should have multiple (2-3 at minimum) high quality visualizations. You can use any Python plotting library to achieve this. Please put these figures in your report. Please also discuss what these visualizations tell you about your data.
		- If the students successfully create the pipeline, and have **2-3 high quality** visualizations, they get 30 points.
	4. **AWS IoT Device Defender (Extra Credit)**: This is an optional portion of the lab, and is extra credit. There are 3 main parts: configuring Audit, configuring Detect, and then using them to report abnormal behavior.
		- If the students successfully configure Audit and Detect, and demonstrate them in action in their report and video, they get 10 points.
	5. Video: 30 points
3. Possible Grade 130/120 (108.3%)