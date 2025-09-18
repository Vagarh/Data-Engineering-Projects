"""
Generador de logs de seguridad sintéticos para testing del pipeline
"""
import os
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from faker import Faker
import ipaddress

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker()


class SecurityLogGenerator:
    def __init__(self):
        self.log_dir = "/app/logs"
        self.logs_per_minute = int(os.getenv('LOGS_PER_MINUTE', '100'))
        self.anomaly_rate = float(os.getenv('ANOMALY_RATE', '0.05'))
        self.log_types = os.getenv('LOG_TYPES', 'web,firewall,auth,system').split(',')
        
        # IPs maliciosas conocidas para simulación
        self.malicious_ips = [
            "192.168.1.100", "10.0.0.50", "172.16.0.25",
            "203.0.113.10", "198.51.100.20", "192.0.2.30"
        ]
        
        # User agents sospechosos
        self.suspicious_user_agents = [
            "sqlmap/1.0",
            "Nikto/2.1.6",
            "Mozilla/5.0 (compatible; Nmap Scripting Engine)",
            "python-requests/2.25.1",
            "curl/7.68.0"
        ]
        
        # Rutas web comunes para ataques
        self.attack_paths = [
            "/admin/login.php",
            "/wp-admin/",
            "/phpmyadmin/",
            "/admin/",
            "/login.php",
            "/admin.php",
            "/administrator/",
            "/wp-login.php",
            "/.env",
            "/config.php"
        ]
        
        # Comandos de inyección SQL
        self.sql_injection_patterns = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --"
        ]
        
        os.makedirs(self.log_dir, exist_ok=True)
    
    def generate_web_log(self, is_anomaly: bool = False) -> Dict[str, Any]:
        """Generar log de servidor web (Apache/Nginx)"""
        timestamp = datetime.now()
        
        if is_anomaly:
            # Generar actividad sospechosa
            ip = random.choice(self.malicious_ips)
            method = random.choice(["POST", "GET", "PUT"])
            path = random.choice(self.attack_paths)
            status_code = random.choice([401, 403, 404, 500])
            user_agent = random.choice(self.suspicious_user_agents)
            
            # Inyección SQL en parámetros
            if "?" not in path and random.random() < 0.5:
                sql_pattern = random.choice(self.sql_injection_patterns)
                path += f"?id={sql_pattern}"
                
        else:
            # Tráfico normal
            ip = fake.ipv4()
            method = random.choice(["GET", "POST", "HEAD"])
            path = random.choice(["/", "/home", "/about", "/contact", "/products", "/api/users"])
            status_code = random.choice([200, 200, 200, 200, 304, 404])
            user_agent = fake.user_agent()
        
        size = random.randint(100, 50000)
        referer = fake.url() if random.random() < 0.3 else "-"
        
        return {
            "timestamp": timestamp.isoformat(),
            "log_type": "web",
            "source_ip": ip,
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_size": size,
            "user_agent": user_agent,
            "referer": referer,
            "processing_time": round(random.uniform(0.01, 2.0), 3),
            "is_anomaly": is_anomaly
        }
    
    def generate_firewall_log(self, is_anomaly: bool = False) -> Dict[str, Any]:
        """Generar log de firewall"""
        timestamp = datetime.now()
        
        if is_anomaly:
            # Actividad sospechosa de firewall
            src_ip = random.choice(self.malicious_ips)
            dst_port = random.choice([22, 23, 3389, 1433, 3306, 5432])  # Puertos sensibles
            action = "DENY"
            protocol = random.choice(["TCP", "UDP"])
            packet_count = random.randint(100, 1000)  # Muchos paquetes = posible escaneo
            
        else:
            # Tráfico normal
            src_ip = fake.ipv4()
            dst_port = random.choice([80, 443, 53, 25, 110, 143])
            action = random.choice(["ALLOW", "ALLOW", "ALLOW", "DENY"])
            protocol = random.choice(["TCP", "UDP", "ICMP"])
            packet_count = random.randint(1, 10)
        
        dst_ip = fake.ipv4_private()
        src_port = random.randint(1024, 65535)
        
        return {
            "timestamp": timestamp.isoformat(),
            "log_type": "firewall",
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": protocol,
            "action": action,
            "packet_count": packet_count,
            "bytes_transferred": random.randint(64, 1500),
            "is_anomaly": is_anomaly
        }
    
    def generate_auth_log(self, is_anomaly: bool = False) -> Dict[str, Any]:
        """Generar log de autenticación"""
        timestamp = datetime.now()
        
        if is_anomaly:
            # Intentos de login sospechosos
            username = random.choice(["admin", "root", "administrator", "test", "guest"])
            src_ip = random.choice(self.malicious_ips)
            result = "FAILED"
            auth_method = random.choice(["password", "ssh_key"])
            failure_reason = random.choice([
                "invalid_password", "account_locked", "invalid_user", "too_many_attempts"
            ])
            
        else:
            # Autenticación normal
            username = fake.user_name()
            src_ip = fake.ipv4_private()
            result = random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "FAILED"])
            auth_method = random.choice(["password", "ssh_key", "mfa"])
            failure_reason = "invalid_password" if result == "FAILED" else None
        
        return {
            "timestamp": timestamp.isoformat(),
            "log_type": "auth",
            "username": username,
            "src_ip": src_ip,
            "result": result,
            "auth_method": auth_method,
            "service": random.choice(["ssh", "rdp", "web", "vpn"]),
            "failure_reason": failure_reason,
            "session_id": fake.uuid4() if result == "SUCCESS" else None,
            "is_anomaly": is_anomaly
        }
    
    def generate_system_log(self, is_anomaly: bool = False) -> Dict[str, Any]:
        """Generar log de sistema"""
        timestamp = datetime.now()
        
        if is_anomaly:
            # Eventos de sistema sospechosos
            event_type = random.choice([
                "process_creation", "file_access", "registry_modification", 
                "network_connection", "privilege_escalation"
            ])
            severity = random.choice(["HIGH", "CRITICAL"])
            process_name = random.choice([
                "powershell.exe", "cmd.exe", "nc.exe", "wget.exe", "curl.exe"
            ])
            
        else:
            # Eventos normales del sistema
            event_type = random.choice([
                "service_start", "service_stop", "user_login", "user_logout",
                "file_access", "process_creation"
            ])
            severity = random.choice(["INFO", "WARNING", "LOW"])
            process_name = random.choice([
                "explorer.exe", "chrome.exe", "notepad.exe", "winlogon.exe"
            ])
        
        return {
            "timestamp": timestamp.isoformat(),
            "log_type": "system",
            "hostname": fake.hostname(),
            "event_type": event_type,
            "severity": severity,
            "process_name": process_name,
            "process_id": random.randint(1000, 9999),
            "user": fake.user_name(),
            "command_line": f"{process_name} {fake.file_path()}" if random.random() < 0.5 else None,
            "parent_process": random.choice(["explorer.exe", "services.exe", "winlogon.exe"]),
            "is_anomaly": is_anomaly
        }
    
    def generate_dns_log(self, is_anomaly: bool = False) -> Dict[str, Any]:
        """Generar log de DNS"""
        timestamp = datetime.now()
        
        if is_anomaly:
            # Consultas DNS sospechosas
            query = random.choice([
                "malware-c2.evil.com",
                "phishing-site.bad.com",
                "crypto-miner.suspicious.org",
                "data-exfil.attacker.net"
            ])
            query_type = "A"
            response_code = random.choice(["NXDOMAIN", "REFUSED"])
            
        else:
            # Consultas DNS normales
            query = random.choice([
                "google.com", "facebook.com", "microsoft.com", "amazon.com",
                "github.com", "stackoverflow.com", fake.domain_name()
            ])
            query_type = random.choice(["A", "AAAA", "MX", "CNAME"])
            response_code = "NOERROR"
        
        return {
            "timestamp": timestamp.isoformat(),
            "log_type": "dns",
            "client_ip": fake.ipv4_private(),
            "query": query,
            "query_type": query_type,
            "response_code": response_code,
            "response_time": round(random.uniform(0.001, 0.1), 3),
            "server_ip": fake.ipv4(),
            "is_anomaly": is_anomaly
        }
    
    def generate_log(self) -> Dict[str, Any]:
        """Generar un log aleatorio"""
        # Determinar si debe ser una anomalía
        is_anomaly = random.random() < self.anomaly_rate
        
        # Seleccionar tipo de log
        log_type = random.choice(self.log_types)
        
        if log_type == "web":
            return self.generate_web_log(is_anomaly)
        elif log_type == "firewall":
            return self.generate_firewall_log(is_anomaly)
        elif log_type == "auth":
            return self.generate_auth_log(is_anomaly)
        elif log_type == "system":
            return self.generate_system_log(is_anomaly)
        elif log_type == "dns":
            return self.generate_dns_log(is_anomaly)
        else:
            return self.generate_web_log(is_anomaly)
    
    def write_log_to_file(self, log_data: Dict[str, Any]):
        """Escribir log a archivo"""
        log_type = log_data["log_type"]
        filename = f"{self.log_dir}/{log_type}.log"
        
        # Formato de log según el tipo
        if log_type == "web":
            log_line = f'{log_data["source_ip"]} - - [{log_data["timestamp"]}] "{log_data["method"]} {log_data["path"]} HTTP/1.1" {log_data["status_code"]} {log_data["response_size"]} "{log_data["referer"]}" "{log_data["user_agent"]}"'
        else:
            # Para otros tipos, usar formato JSON
            log_line = json.dumps(log_data)
        
        with open(filename, "a") as f:
            f.write(log_line + "\n")
    
    def run_continuous(self):
        """Ejecutar generador de forma continua"""
        logger.info(f"Iniciando generador de logs: {self.logs_per_minute} logs/min, {self.anomaly_rate*100}% anomalías")
        
        interval = 60.0 / self.logs_per_minute  # Intervalo entre logs
        
        while True:
            try:
                log_data = self.generate_log()
                self.write_log_to_file(log_data)
                
                if log_data.get("is_anomaly"):
                    logger.warning(f"Anomalía generada: {log_data['log_type']} - {log_data.get('source_ip', log_data.get('src_ip', 'N/A'))}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Deteniendo generador...")
                break
            except Exception as e:
                logger.error(f"Error generando log: {e}")
                time.sleep(1)


if __name__ == "__main__":
    generator = SecurityLogGenerator()
    generator.run_continuous()