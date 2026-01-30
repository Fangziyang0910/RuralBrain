FROM ruralbrain-pest-detector:latest

WORKDIR /app
ENV YOLO_CONFIG_DIR=/app/ultralytics

# 复制三个服务的完整代码
COPY src/algorithms/pest_detection/detector ./pest/
COPY src/algorithms/rice_detection/detector ./rice/
COPY src/algorithms/cow_detection/detector ./cow/

# 确保 appuser 对目录有写权限（用于 uploads 和运行时文件）
USER root
RUN mkdir -p /app/pest/uploads /app/rice/uploads /app/cow/uploads /app/ultralytics && \
    chown -R appuser:appuser /app
USER appuser

# 复制启动脚本并转换换行符
COPY src/algorithms/triple_detector/start_all.sh .
RUN sed -i 's/\r$//' start_all.sh

# 暴露三个端口
EXPOSE 8001 8081 8002

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health && \
        curl -f http://localhost:8081/health && \
        curl -f http://localhost:8002/health || exit 1

# 启动所有服务
CMD ["bash", "start_all.sh"]
