import praw
import networkx as nx
import matplotlib.pyplot as plt
import time

# Reddit API Credentials
reddit = praw.Reddit(
    client_id="MVXPviyN_QslE-BqnbpzRA",
    client_secret="V1aBLhLQ9uCUOAvNTtdf98TvM4khEg",
    user_agent="reddit_network_analysis_v1 by u/Phappyi"
)

# Enable automatic rate limit handling
reddit.config.retry_on_rate_limit = True

# Choose a subreddit
subreddit_name = "UMD"
subreddit = reddit.subreddit(subreddit_name)

print("Fetching posts...")

# Extract the top 10 posts (change if needed)
# Fetch posts from subreddit
posts = []
for i, post in enumerate(subreddit.top(limit=10)):  # Start with 10 to test
    if isinstance(post, praw.models.reddit.submission.Submission):  # Ensure the post is a Submission object
        posts.append(post)
        print(f"Fetched post {i+1}: {post.title}")
    else:
        print(f"Skipping post {i+1}: Not a valid Reddit post object.")
    time.sleep(2)  # Slow down requests

# Now proceed with processing the posts and comments

print("Fetching comments...")

# Store user interactions
edges = []
parent_comment_cache = {}  # Cache to store parent comments

for i, post in enumerate(posts):
    if hasattr(post, 'author') and post.author:  # Check if the post has an author attribute
        post_author = post.author.name
    else:
        post_author = "[deleted]"

    print(f"Processing post {i+1}: {post.title}")

    # Extract comments (Limit depth to avoid too many requests)
    post.comments.replace_more(limit=2)  # Load only a few comments
    comments = post.comments.list()  # Get all comments after replacing "more_comments"
    comment_count = 0

    for j, comment in enumerate(comments):
        if hasattr(comment, 'author') and comment.author:  # Check if the comment has an author attribute
            commenter = comment.author.name
        else:
            commenter = "[deleted]"

        edges.append((commenter, post_author))  # Edge from commenter to post author
        comment_count += 1

        # Also add reply relationships
        if comment.parent_id.startswith("t1_"):  # "t1_" means it's a comment reply
            parent_id = comment.parent_id.split("_")[1]

            # Check cache before making an API call
            if parent_id in parent_comment_cache:
                parent_author = parent_comment_cache[parent_id]
            else:
                try:
                    parent_comment = reddit.comment(id=parent_id)
                    parent_author = parent_comment.author.name if parent_comment.author else "[deleted]"
                    parent_comment_cache[parent_id] = parent_author  # Store in cache
                    time.sleep(2)  # Slow down API requests
                except Exception as e:
                    print(f"    Error fetching parent comment {parent_id}: {e}")
                    parent_author = "[deleted]"

            edges.append((commenter, parent_author))  # Edge from commenter to parent

        # Stop if too many comments (to prevent getting stuck)
        if comment_count >= 30:
            print("    Skipping remaining comments to prevent overload.")
            break

    print(f"  Processed {comment_count} comments for post {i+1}")




# Remove self-loops
edges = [(a, b) for a, b in edges if a != b]

# Create Graph
G = nx.Graph()
G.add_edges_from(edges)

# Degree Centrality
degree_centrality = nx.degree_centrality(G)
top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
print(f"Top 5 by Degree Centrality: {top_degree}")

# Betweenness Centrality
betweenness_centrality = nx.betweenness_centrality(G)
top_betweenness = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
print(f"Top 5 by Betweenness Centrality: {top_betweenness}")

# Eigenvector Centrality
eigenvector_centrality = nx.eigenvector_centrality(G)
top_eigenvector = sorted(eigenvector_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
print(f"Top 5 by Eigenvector Centrality: {top_eigenvector}")

# Remove '[deleted]' users from the network
G.remove_nodes_from([node for node in G.nodes if node == '[deleted]'])

# Filter out low-activity users (example: users with less than 2 interactions)
low_activity_users = [node for node, degree in G.degree() if degree < 2]
G.remove_nodes_from(low_activity_users)

# Recompute Degree Centrality after removing nodes
degree_centrality = nx.degree_centrality(G)

# Visualize the network with node size proportional to degree centrality
node_size = [v * 1000 for v in degree_centrality.values()]  # Scale factor for node size

# Draw the graph with custom node sizes
plt.figure(figsize=(12, 12))  # Adjust the figure size if needed
nx.draw(G, with_labels=True, node_size=node_size, node_color='blue', font_size=10, font_color='black', alpha=0.7, edge_color='gray')
plt.title(f'Reddit Network for {subreddit_name}')
plt.show()


# Print basic graph info
print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

# Save graph
nx.write_edgelist(G, "reddit_network.edgelist")

print("Graph saved successfully!")

