# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import threading
import time
from datetime import datetime
import pandas as pd
import sqlite3

# Import our custom modules
from web_crawler import WebCrawler
from database_manager import DatabaseManager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize database
db_manager = DatabaseManager(db_type="sqlite", connection_params={"db_path": "crawler_data.db"})

# Store active crawlers
active_crawlers = {}
crawl_status = {}

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/start_crawl', methods=['POST'])
def start_crawl():
    """Start a new crawl job."""
    try:
        start_url = request.form.get('start_url')
        max_depth = int(request.form.get('max_depth', 3))
        use_selenium = request.form.get('use_selenium') == 'on'
        restrict_domain = request.form.get('restrict_domain') == 'on'
        
        # Get selectors for data extraction
        selectors = {}
        for i in range(1, 6):  # Support up to 5 fields
            field = request.form.get(f'field_{i}')
            selector = request.form.get(f'selector_{i}')
            if field and selector:
                selectors[field] = selector
        
        if not start_url:
            flash('Start URL is required', 'error')
            return redirect(url_for('index'))
            
        # Generate a unique job ID
        job_id = f"job_{int(time.time())}"
        
        # Initialize crawler
        crawler = WebCrawler(database_manager=db_manager, use_selenium=use_selenium)
        active_crawlers[job_id] = crawler
        
        # Initialize status
        crawl_status[job_id] = {
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'start_url': start_url,
            'max_depth': max_depth,
            'pages_crawled': 0,
            'errors': 0,
            'completed': False
        }
        
        # Start crawling in a separate thread
        def crawl_task():
            try:
                data = crawler.crawl(
                    start_url=start_url,
                    max_depth=max_depth,
                    selectors=selectors,
                    restrict_domain=restrict_domain
                )
                
                # Update status when complete
                crawl_status[job_id]['status'] = 'completed'
                crawl_status[job_id]['pages_crawled'] = len(crawler.visited_urls)
                crawl_status[job_id]['completed'] = True
                crawl_status[job_id]['end_time'] = datetime.now().isoformat()
                
            except Exception as e:
                crawl_status[job_id]['status'] = 'error'
                crawl_status[job_id]['error_message'] = str(e)
                crawl_status[job_id]['errors'] += 1
                crawl_status[job_id]['completed'] = True
                crawl_status[job_id]['end_time'] = datetime.now().isoformat()
            finally:
                crawler.close()
                
        thread = threading.Thread(target=crawl_task)
        thread.daemon = True
        thread.start()
        
        flash(f'Crawl job started with ID: {job_id}', 'success')
        return redirect(url_for('job_status', job_id=job_id))
        
    except Exception as e:
        flash(f'Error starting crawl: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/job_status/<job_id>')
def job_status(job_id):
    """Show status of a specific job."""
    if job_id not in crawl_status:
        flash(f'Job {job_id} not found', 'error')
        return redirect(url_for('index'))
        
    return render_template('job_status.html', job_id=job_id, status=crawl_status[job_id])

@app.route('/api/job_status/<job_id>')
def api_job_status(job_id):
    """API endpoint to get job status."""
    if job_id not in crawl_status:
        return jsonify({'error': 'Job not found'}), 404
        
    return jsonify(crawl_status[job_id])

@app.route('/stop_job/<job_id>')
def stop_job(job_id):
    """Stop a running job."""
    if job_id in active_crawlers:
        try:
            crawler = active_crawlers[job_id]
            crawler.close()
            
            # Update status
            crawl_status[job_id]['status'] = 'stopped'
            crawl_status[job_id]['completed'] = True
            crawl_status[job_id]['end_time'] = datetime.now().isoformat()
            
            flash(f'Job {job_id} stopped successfully', 'success')
        except Exception as e:
            flash(f'Error stopping job: {str(e)}', 'error')
    else:
        flash(f'Job {job_id} not found or already completed', 'error')
        
    return redirect(url_for('job_status', job_id=job_id))

@app.route('/jobs')
def list_jobs():
    """List all jobs."""
    return render_template('jobs.html', jobs=crawl_status)

@app.route('/data')
def data_explorer():
    """Explore crawled data."""
    # Get filter parameters
    url_filter = request.args.get('url_filter', '')
    limit = int(request.args.get('limit', 100))
    
    # Get data from database
    data = db_manager.get_data(url=url_filter if url_filter else None, limit=limit)
    
    return render_template('data_explorer.html', data=data, url_filter=url_filter, limit=limit)

@app.route('/api/data')
def api_data():
    """API endpoint to get crawled data."""
    url_filter = request.args.get('url_filter', '')
    limit = int(request.args.get('limit', 100))
    
    data = db_manager.get_data(url=url_filter if url_filter else None, limit=limit)
    return jsonify(data)

@app.route('/export/<format>')
def export_data(format):
    """Export crawled data in CSV or JSON format."""
    url_filter = request.args.get('url_filter', '')
    limit = int(request.args.get('limit', 1000))
    
    data = db_manager.get_data(url=url_filter if url_filter else None, limit=limit)
    
    if format.lower() == 'csv':
        # Convert to DataFrame and then to CSV
        df = pd.DataFrame(data)
        csv_data = df.to_csv(index=False)
        
        # Prepare response
        response = app.response_class(
            response=csv_data,
            status=200,
            mimetype='text/csv'
        )
        response.headers["Content-Disposition"] = "attachment; filename=crawler_data.csv"
        return response
        
    elif format.lower() == 'json':
        # Convert to JSON
        json_data = json.dumps(data, indent=2, default=str)
        
        # Prepare response
        response = app.response_class(
            response=json_data,
            status=200,
            mimetype='application/json'
        )
        response.headers["Content-Disposition"] = "attachment; filename=crawler_data.json"
        return response
    
    else:
        flash(f'Unsupported export format: {format}', 'error')
        return redirect(url_for('data_explorer'))

@app.route('/visualize')
def visualize_data():
    """Visualize crawled data."""
    return render_template('visualize.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint to get statistics about crawled data."""
    # Get statistics from database
    conn = sqlite3.connect(db_manager.connection_params.get("db_path", "crawler_data.db"))
    cursor = conn.cursor()
    
    stats = {}
    
    # Total number of pages crawled
    cursor.execute("SELECT COUNT(*) FROM crawled_pages")
    stats['total_pages'] = cursor.fetchone()[0]
    
    # Top domains
    cursor.execute("""
    SELECT 
        substr(url, instr(url, '://') + 3, 
            case 
                when instr(substr(url, instr(url, '://') + 3), '/') = 0 
                then length(substr(url, instr(url, '://') + 3)) 
                else instr(substr(url, instr(url, '://') + 3), '/') - 1 
            end
        ) as domain,
        COUNT(*) as count
    FROM crawled_pages
    GROUP BY domain
    ORDER BY count DESC
    LIMIT 10
    """)
    stats['top_domains'] = [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    # Crawl activity over time
    cursor.execute("""
    SELECT 
        substr(crawl_date, 1, 10) as date,
        COUNT(*) as count
    FROM crawled_pages
    GROUP BY date
    ORDER BY date
    """)
    stats['activity_by_date'] = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True)