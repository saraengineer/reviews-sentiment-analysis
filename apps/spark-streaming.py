from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
KAFKA_TOPIC_SOURCE = "reviews"


spark = SparkSession.builder.appName("sentiment_analysis_reviews").getOrCreate()
# Reduce logging
spark.sparkContext.setLogLevel("WARN")

df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
    .option("subscribe", KAFKA_TOPIC_SOURCE) \
    .option("startingOffsets", "earliest") \
    .load()

json_schema = StructType([

  StructField("reviewId", StringType()),

  StructField("review", StringType()),

  StructField("user", StringType())

])


review_df = df.select(from_json(col("value").cast("string"), json_schema).alias("value"))

review_df.printSchema()


# analyze sentiment
def analyze_sentiment(review):
    # I choose NLTK model, you can replace it with another sentiment analysis model
    sia = SentimentIntensityAnalyzer()
    sentiment_scores = sia.polarity_scores(review)
    
    return str(sentiment_scores)



sentiment_udf = udf(analyze_sentiment, StringType())

# Apply the sentiment analysis UDF to the "review" field
processed_stream_df = review_df.withColumn("sentiment", sentiment_udf(col("value.review")))

# Select the desired columns to output
output_df = processed_stream_df.select(
    col("value.reviewId"),
    col("value.review"),
    col("value.user"),
    col("sentiment")
)


# Write the stream to the console 
query = output_df \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", "false") \
    .start()

query.awaitTermination()
