
from flask import Blueprint, jsonify, request
import logging
import json
from datetime import datetime

# Import our custom modules
from database_manager import DatabaseManager

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Blueprint
api = Blueprint('api', __name__)

# Initialize database connection
db_manager = DatabaseManager(db_type="sqlite", connection_params={"db_path": "crawler_data.db"})

@api.route('/jobs', methods=['GET'])
def get_jobs():
    """API endpoint to get all jobs."""
    # Import here to avoid circular imports
    from app import crawl_status
    return jsonify(crawl_status)

@api.route('/job_status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """API endpoint to get job status."""
    # Import here to avoid circular imports
    from app import crawl_status
    
    if job_id not in crawl_status:
        return jsonify({'error': 'Job not found'}), 404
        
    return jsonify(crawl_status[job_id])

@api.route('/data', methods=['GET'])
def get_data():
    """API endpoint to get crawled data."""
    url_filter = request.args.get('url_filter', '')
    limit = int(request.args.get('limit', 100))
    
    data = db_manager.get_data(url=url_filter if url_filter else None, limit=limit)
    return jsonify(data)

@api.route('/stats', methods=['GET'])
def get_stats():
    """API endpoint to get statistics about crawled data."""
    import sqlite3
    
    # Get statistics from database
    conn = sqlite3.connect(db_manager.connection_params.get("db_path", "crawler_data.db"))
    cursor = conn.cursor()
    
    stats = {}
    
    try:
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
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        stats['error'] = "Database error occurred"
    finally:
        conn.close()
    
    return jsonify(stats)

@api.route('/export/<format>', methods=['GET'])
def export_data(format):
    """API endpoint to export data in various formats."""
    import pandas as pd
    
    url_filter = request.args.get('url_filter', '')
    limit = int(request.args.get('limit', 1000))
    
    data = db_manager.get_data(url=url_filter if url_filter else None, limit=limit)
    
    if format.lower() == 'csv':
        # Convert to DataFrame and then to CSV
        df = pd.DataFrame(data)
        csv_data = df.to_csv(index=False)
        
        response = jsonify({
            'data': csv_data,
            'filename': 'crawler_data.csv',
            'mime_type': 'text/csv'
        })
        return response
        
    elif format.lower() == 'json':
        # Return data as JSON
        return jsonify(data)
    
    else:
        return jsonify({'error': f'Unsupported export format: {format}'}), 400