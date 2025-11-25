import random
import time
import uuid
from fpdf import FPDF
from datetime import datetime, timedelta

# Configuration for volume (approx 50-60 lines per page)
PAGES_PER_DOC = 12 
LINES_PER_PAGE = 50
TOTAL_LINES = PAGES_PER_DOC * LINES_PER_PAGE

class PDFGenerator(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'CONFIDENTIAL - INTERNAL USE ONLY', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Courier', '', 10) # Monospace for logs/tech data
        self.multi_cell(0, 5, body)
        self.ln()

def generate_sdd_pdf():
    pdf = PDFGenerator()
    pdf.add_page()
    pdf.chapter_title("1. TitanCore System Design Document (v2.4.1)")
    
    # Intro content
    intro = """
    1.1 Executive Summary
    TitanCore is a high-throughput, fault-tolerant microservices architecture designed to handle 50,000 TPS.
    
    1.2 Architecture Overview
    The system utilizes a hexagonal architecture. The core domain logic is isolated from external layers.
    """
    pdf.chapter_body(intro)

    # Generate bulk technical content
    components = ["LedgerService", "PaymentGateway", "RiskEngine", "NotificationService", "AuditLog", "ReconModule"]
    patterns = ["CircuitBreaker", "SagaPattern", "EventSourcing", "CQRS", "Sharding"]
    
    for i in range(1, 40): # Generate sections
        comp = random.choice(components)
        pat = random.choice(patterns)
        title = f"2.{i} Component Specification: {comp} (Shard {i})"
        pdf.chapter_title(title)
        
        body = f"""
        2.{i}.1 Overview
        The {comp} module is responsible for handling high-volume traffic using the {pat} pattern. 
        It connects to the underlying Cassandra cluster on port 9042.
        
        2.{i}.2 Data Consistency
        To ensure ACID properties, we utilize a two-phase commit where applicable, falling back to 
        eventual consistency for read models. 
        
        2.{i}.3 Scaling Policy
        Autoscaling is triggered when CPU > 75% or Memory > 80%.
        Min Replicas: 3
        Max Replicas: 50
        
        2.{i}.4 Interface Definition
        Endpoint: POST /api/v1/{comp.lower()}/process
        Payload: JSON
        Timeout: 5000ms
        Retry Strategy: Exponential Backoff (Multiplier 1.5)
        
        [Detailed Architecture notes for {comp} continued...]
        The internal buffer size is set to 1024KB. Memory management is handled via G1GC.
        """
        pdf.chapter_body(body)
        
    pdf.output("1_System_Design_Document.pdf")
    print("Generated: 1_System_Design_Document.pdf")

def generate_logs_pdf():
    pdf = PDFGenerator()
    pdf.add_page()
    pdf.chapter_title("2. System & Application Logs (Production)")
    
    start_time = datetime.now() - timedelta(days=1)
    
    log_levels = ["INFO", "INFO", "INFO", "WARN", "DEBUG", "ERROR"]
    services = ["TxController", "AuthService", "LedgerWriter", "KafkaConsumer", "RiskEngine"]
    messages = [
        "Connection established to database pool.",
        "Payload validated successfully.",
        "User session token refreshed.",
        "Latency spike detected (150ms).",
        "Garbage collection executed.",
        "Message published to topic 'tx_settled'.",
        "Cache miss for key user_12345.",
        "Rate limit quota remaining: 4500."
    ]
    
    log_buffer = ""
    for i in range(TOTAL_LINES):
        current_time = start_time + timedelta(milliseconds=random.randint(10, 500))
        start_time = current_time
        level = random.choice(log_levels)
        svc = random.choice(services)
        msg = random.choice(messages)
        
        # Inject occasional errors
        if level == "ERROR":
            msg = f"NullPointerException in module {svc}. Stacktrace: com.titancore.impl.Service.java:42"
        
        line = f"{current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} [{level:<5}] [{svc}] - {msg}\n"
        log_buffer += line
        
        # Flush to PDF every 50 lines to manage memory
        if i % 50 == 0:
            pdf.chapter_body(log_buffer)
            log_buffer = ""
            
    pdf.output("2_Production_Logs.pdf")
    print("Generated: 2_Production_Logs.pdf")

def generate_defects_pdf():
    pdf = PDFGenerator()
    pdf.add_page()
    pdf.chapter_title("3. Open Defect Tickets Export")
    
    statuses = ["Open", "In Progress", "Blocked", "Ready for QA"]
    priorities = ["P1-Critical", "P2-High", "P3-Medium", "P4-Low"]
    titles = [
        "Memory leak in export service", "UI Button misaligned on mobile", 
        "API returns 500 on valid payload", "Database timeout during backup",
        "Kafka consumer lag increasing", "Login page CSS broken in Safari",
        "incorrect decimal rounding in Tax calc"
    ]
    
    for i in range(100): # 100 tickets will easily fill 10 pages
        ticket_id = f"DEF-{2000+i}"
        title = random.choice(titles)
        priority = random.choice(priorities)
        status = random.choice(statuses)
        
        block = f"""
        -------------------------------------------------------
        Ticket ID:   {ticket_id}
        Title:       {title}
        Priority:    {priority}
        Status:      {status}
        Assignee:    Developer_{random.randint(1,20)}
        Created:     2023-10-{random.randint(1,30)}
        
        Description:
        The user reported an issue where {title.lower()}. 
        Steps to Reproduce:
        1. Login as Admin
        2. Navigate to Settings
        3. Click on module X
        
        Expected: Action completes successfully.
        Actual: System throws an exception or hangs.
        
        Logs Attached:
        Error: timeout waiting for resource lock.
        -------------------------------------------------------
        """
        pdf.chapter_body(block)

    pdf.output("3_Defect_Tickets.pdf")
    print("Generated: 3_Defect_Tickets.pdf")

def generate_rca_pdf():
    pdf = PDFGenerator()
    pdf.add_page()
    pdf.chapter_title("4. Root Cause Analysis (RCA) Archive")
    
    incidents = [
        ("INC-401", "Database CPU Spike"),
        ("INC-402", "Payment Gateway Timeout"),
        ("INC-403", "DDoS Attack on API"),
        ("INC-404", "Memory Exhaustion in Report Pod"),
        ("INC-405", "Redis Cache Fragmentation")
    ]
    
    # Repeat incidents to fill pages
    for i in range(20): 
        inc = random.choice(incidents)
        inc_id = f"{inc[0]}-{i}"
        
        block = f"""
        =======================================================
        Incident Report: {inc_id}
        Subject:         {inc[1]}
        Date:            2024-01-{random.randint(1,28)}
        Duration:        {random.randint(10, 120)} Minutes
        Severity:        Sev-1
        =======================================================
        
        1. Problem Statement
        The monitoring system alerted high latency and error rates in the {inc[1]} module.
        Users experienced 503 errors.
        
        2. Root Cause Analysis (5 Whys)
        - Why failed? The connection pool was exhausted.
        - Why exhausted? Threads were waiting on I/O.
        - Why waiting? The external vendor API was slow.
        - Why slow? Vendor was undergoing maintenance.
        - Root Cause: Lack of circuit breaker configuration for vendor maintenance windows.
        
        3. Resolution
        Restarted the pods and enabled the fallback mocked response feature.
        
        4. Prevention / Action Items
        [ ] Implement Hystrix Circuit Breaker (Due: Jan 30)
        [ ] Increase timeout thresholds (Due: Jan 25)
        [ ] Add alerting for connection pool saturation.
        
        5. Timeline
        08:00 - Alert fired
        08:05 - Sev-1 declared
        08:15 - Root cause identified
        08:30 - Fix deployed
        =======================================================
        """
        pdf.chapter_body(block)

    pdf.output("4_RCA_Reports.pdf")
    print("Generated: 4_RCA_Reports.pdf")

if __name__ == "__main__":
    generate_sdd_pdf()
    generate_logs_pdf()
    generate_defects_pdf()
    generate_rca_pdf()
    print("Done! All 4 PDFs generated.")