uration
        self.max_concurrent_executions = 3
        self.default_timeout = 300  # 5 minutes
        self.retry_attempts = 3
        self.adaptive_timing = True
        
        # Callbacks
        self.on_execution_queued: Optional[Callable[[str, AutomationProfile], None]] = None
        self.on_execution_started: Optional[Callable[[str, AutomationProfile], None]] = None
        self.on_execution_completed: Optional[Callable[[str, ExecutionResult, Dict[str, Any]], None]] = None
        self.on_execution_failed: Optional[Callable[[str, Exception], None]] = None
        
        self.logger.info("ExecutionEngine initialized")
    
    def execute_profile(self, profile: AutomationProfile,
                       mode: ExecutionMode = ExecutionMode.NORMAL,
                       priority: ExecutionPriority = ExecutionPriority.NORMAL,
                       user_variables: Dict[str, Any] = None,
                       timeout: Optional[int] = None) -> str:
        """
        Queue profile for execution
        
        Args:
            profile: Profile to execute
            mode: Execution mode
            priority: Execution priority
            user_variables: User-provided variables
            timeout: Execution timeout in seconds
            
        Returns:
            Execution ID for tracking
        """
        execution_id = self._generate_execution_id(profile)
        
        execution_request = {
            'execution_id': execution_id,
            'profile': profile,
            'mode': mode,
            'priority': priority,
            'user_variables': user_variables or {},
            'timeout': timeout or self.default_timeout,
            'queued_at': datetime.now(),
            'retry_count': 0,
            'status': 'queued'
        }
        
        # Add to queue based on priority
        self._add_to_queue(execution_request)
        
        # Callback
        if self.on_execution_queued:
            self.on_execution_queued(execution_id, profile)
        
        self.logger.info(f"Profile queued for execution: {profile.name} (ID: {execution_id})")
        
        # Start processing if not already running
        self._process_queue()
        
        return execution_id
    
    def execute_profile_immediate(self, profile: AutomationProfile,
                                mode: ExecutionMode = ExecutionMode.NORMAL,
                                user_variables: Dict[str, Any] = None) -> ExecutionResult:
        """
        Execute profile immediately (blocking)
        
        Args:
            profile: Profile to execute
            mode: Execution mode
            user_variables: User-provided variables
            
        Returns:
            ExecutionResult
        """
        self.logger.info(f"Executing profile immediately: {profile.name}")
        
        try:
            # Pre-execution analysis
            analysis = self._analyze_execution_feasibility(profile)
            if not analysis['feasible']:
                self.logger.warning(f"Execution not feasible: {analysis['reason']}")
                return ExecutionResult.FAILURE
            
            # Apply intelligent optimizations
            optimizations = self._get_execution_optimizations(profile, mode)
            self._apply_optimizations(optimizations)
            
            # Execute with context management
            context = self.context_manager.initialize_context(profile, user_variables)
            
            # Adapt execution based on environment
            adaptations = self.context_manager.adapt_to_environment()
            self._apply_adaptations(adaptations)
            
            # Execute profile
            result = self.executor.execute_profile(profile, user_variables, mode.value)
            
            # Post-execution analysis
            insights = self.context_manager.get_execution_insights()
            self._record_execution_metrics(profile, result, insights)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Immediate execution failed: {e}")
            return ExecutionResult.FAILURE
        finally:
            self.context_manager.cleanup_context()
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel queued or active execution"""
        # Check if in queue
        for i, request in enumerate(self.execution_queue):
            if request['execution_id'] == execution_id:
                self.execution_queue.pop(i)
                self.logger.info(f"Cancelled queued execution: {execution_id}")
                return True
        
        # Check if active
        if execution_id in self.active_executions:
            # Cancel active execution
            self.executor.cancel_execution()
            self.active_executions[execution_id]['status'] = 'cancelled'
            self.logger.info(f"Cancelled active execution: {execution_id}")
            return True
        
        return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of execution"""
        # Check active executions
        if execution_id in self.active_executions:
            return self.active_executions[execution_id].copy()
        
        # Check queue
        for request in self.execution_queue:
            if request['execution_id'] == execution_id:
                return {
                    'execution_id': execution_id,
                    'status': 'queued',
                    'position_in_queue': self.execution_queue.index(request) + 1,
                    'queued_at': request['queued_at']
                }
        
        # Check history
        for record in self.execution_history:
            if record['execution_id'] == execution_id:
                return record.copy()
        
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get execution queue status"""
        return {
            'queue_length': len(self.execution_queue),
            'active_executions': len(self.active_executions),
            'max_concurrent': self.max_concurrent_executions,
            'queued_profiles': [
                {
                    'execution_id': req['execution_id'],
                    'profile_name': req['profile'].name,
                    'priority': req['priority'].name,
                    'queued_at': req['queued_at'].isoformat()
                }
                for req in self.execution_queue
            ],
            'active_profiles': [
                {
                    'execution_id': exec_id,
                    'profile_name': exec_data['profile'].name,
                    'started_at': exec_data['started_at'].isoformat(),
                    'status': exec_data['status']
                }
                for exec_id, exec_data in self.active_executions.items()
            ]
        }
    
    def get_execution_recommendations(self, profile: AutomationProfile) -> List[Dict[str, Any]]:
        """Get intelligent execution recommendations"""
        recommendations = []
        
        try:
            # Analyze current system state
            analysis = self._analyze_execution_feasibility(profile)
            
            if not analysis['feasible']:
                recommendations.append({
                    'type': 'warning',
                    'message': f"Execution not recommended: {analysis['reason']}",
                    'confidence': 0.9
                })
            
            # Get context-aware suggestions
            context_suggestions = self.context_manager.get_intelligent_suggestions("pre_execution")
            recommendations.extend(context_suggestions)
            
            # Analyze optimal timing
            timing_analysis = self._analyze_optimal_timing(profile)
            if timing_analysis['optimal_time'] != 'now':
                recommendations.append({
                    'type': 'timing',
                    'message': f"Consider executing at {timing_analysis['optimal_time']} for better results",
                    'confidence': timing_analysis['confidence']
                })
            
            # Resource optimization suggestions
            resource_suggestions = self._get_resource_optimization_suggestions(profile)
            recommendations.extend(resource_suggestions)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return []
    
    def optimize_profile_execution(self, profile: AutomationProfile) -> Dict[str, Any]:
        """Get optimization suggestions for profile execution"""
        optimizations = {}
        
        try:
            # Analyze profile structure
            structure_analysis = self._analyze_profile_structure(profile)
            optimizations.update(structure_analysis)
            
            # Analyze execution patterns
            pattern_analysis = self._analyze_execution_patterns(profile)
            optimizations.update(pattern_analysis)
            
            # Resource optimization
            resource_optimization = self._optimize_resource_usage(profile)
            optimizations.update(resource_optimization)
            
            # Timing optimization
            timing_optimization = self._optimize_execution_timing(profile)
            optimizations.update(timing_optimization)
            
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Failed to optimize profile execution: {e}")
            return {}
    
    # Private methods
    
    def _generate_execution_id(self, profile: AutomationProfile) -> str:
        """Generate unique execution ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{profile.name}_{timestamp}"
    
    def _add_to_queue(self, execution_request: Dict[str, Any]):
        """Add execution request to queue based on priority"""
        priority = execution_request['priority']
        
        # Find insertion point based on priority
        insertion_index = len(self.execution_queue)
        for i, existing_request in enumerate(self.execution_queue):
            if existing_request['priority'].value < priority.value:
                insertion_index = i
                break
        
        self.execution_queue.insert(insertion_index, execution_request)
    
    def _process_queue(self):
        """Process execution queue"""
        if len(self.active_executions) >= self.max_concurrent_executions:
            return
        
        if not self.execution_queue:
            return
        
        # Get next execution request
        request = self.execution_queue.pop(0)
        execution_id = request['execution_id']
        
        # Move to active executions
        request['status'] = 'starting'
        request['started_at'] = datetime.now()
        self.active_executions[execution_id] = request
        
        # Start execution asynchronously
        asyncio.create_task(self._execute_async(request))
    
    async def _execute_async(self, request: Dict[str, Any]):
        """Execute profile asynchronously"""
        execution_id = request['execution_id']
        profile = request['profile']
        
        try:
            # Callback
            if self.on_execution_started:
                self.on_execution_started(execution_id, profile)
            
            # Update status
            self.active_executions[execution_id]['status'] = 'running'
            
            # Execute profile
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._execute_with_retry,
                request
            )
            
            # Update status
            self.active_executions[execution_id]['status'] = 'completed'
            self.active_executions[execution_id]['result'] = result
            self.active_executions[execution_id]['completed_at'] = datetime.now()
            
            # Callback
            if self.on_execution_completed:
                self.on_execution_completed(execution_id, result, request)
            
            # Move to history
            self._move_to_history(execution_id)
            
        except Exception as e:
            self.logger.error(f"Async execution failed: {e}")
            
            # Update status
            self.active_executions[execution_id]['status'] = 'failed'
            self.active_executions[execution_id]['error'] = str(e)
            self.active_executions[execution_id]['completed_at'] = datetime.now()
            
            # Callback
            if self.on_execution_failed:
                self.on_execution_failed(execution_id, e)
            
            # Move to history
            self._move_to_history(execution_id)
        
        finally:
            # Continue processing queue
            self._process_queue()
    
    def _execute_with_retry(self, request: Dict[str, Any]) -> ExecutionResult:
        """Execute profile with retry logic"""
        profile = request['profile']
        mode = request['mode']
        user_variables = request['user_variables']
        max_retries = self.retry_attempts
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt} for profile: {profile.name}")
                    # Add delay between retries
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                
                # Execute profile
                result = self.executor.execute_profile(profile, user_variables, mode.value)
                
                if result == ExecutionResult.SUCCESS:
                    return result
                elif result in [ExecutionResult.PARTIAL, ExecutionResult.FAILURE]:
                    if attempt < max_retries:
                        continue  # Retry
                    else:
                        return result
                else:
                    return result  # Don't retry for CANCELLED or TIMEOUT
                    
            except Exception as e:
                if attempt < max_retries:
                    self.logger.warning(f"Execution attempt {attempt + 1} failed, retrying: {e}")
                    continue
                else:
                    raise
        
        return ExecutionResult.FAILURE
    
    def _move_to_history(self, execution_id: str):
        """Move execution from active to history"""
        if execution_id in self.active_executions:
            execution_data = self.active_executions.pop(execution_id)
            self.execution_history.append(execution_data)
            
            # Keep only recent history (last 100 executions)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
    
    def _analyze_execution_feasibility(self, profile: AutomationProfile) -> Dict[str, Any]:
        """Analyze if execution is feasible"""
        analysis = {'feasible': True, 'reason': None, 'confidence': 1.0}
        
        try:
            # Check if integration bridge is available
            if not self.integration_bridge.is_available():
                analysis['feasible'] = False
                analysis['reason'] = 'Integration components not available'
                return analysis
            
            # Check system resources
            context = self.context_manager._gather_system_context()
            cpu_usage = context.get('cpu_percent', 0)
            memory_usage = context.get('memory_percent', 0)
            
            if cpu_usage > 90:
                analysis['feasible'] = False
                analysis['reason'] = 'System CPU usage too high'
                return analysis
            
            if memory_usage > 95:
                analysis['feasible'] = False
                analysis['reason'] = 'System memory usage too high'
                return analysis
            
            # Check target application availability
            if profile.target_application:
                if not self.integration_bridge.is_application_running(profile.target_application):
                    analysis['confidence'] = 0.7
                    analysis['reason'] = f'Target application "{profile.target_application}" not running'
            
            return analysis
            
        except Exception as e:
            analysis['feasible'] = False
            analysis['reason'] = f'Analysis failed: {str(e)}'
            return analysis
    
    def _get_execution_optimizations(self, profile: AutomationProfile, 
                                   mode: ExecutionMode) -> Dict[str, Any]:
        """Get execution optimizations"""
        optimizations = {}
        
        try:
            # Mode-specific optimizations
            if mode == ExecutionMode.PERFORMANCE:
                optimizations['reduce_delays'] = True
                optimizations['parallel_actions'] = True
                optimizations['skip_screenshots'] = True
            elif mode == ExecutionMode.SAFE_MODE:
                optimizations['increase_delays'] = True
                optimizations['extra_validation'] = True
                optimizations['screenshot_on_every_step'] = True
            
            # Profile-specific optimizations
            if len(profile.regions) > 10:
                optimizations['region_caching'] = True
            
            if len(profile.rules) > 5:
                optimizations['rule_parallelization'] = True
            
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Failed to get optimizations: {e}")
            return {}
    
    def _apply_optimizations(self, optimizations: Dict[str, Any]):
        """Apply execution optimizations"""
        try:
            for optimization, value in optimizations.items():
                if optimization == 'reduce_delays' and value:
                    # Reduce default delays
                    pass
                elif optimization == 'increase_delays' and value:
                    # Increase default delays
                    pass
                # Add more optimization implementations
                
        except Exception as e:
            self.logger.error(f"Failed to apply optimizations: {e}")
    
    def _apply_adaptations(self, adaptations: Dict[str, Any]):
        """Apply environmental adaptations"""
        try:
            for adaptation, value in adaptations.items():
                if adaptation == 'timing_multiplier':
                    # Adjust timing based on system load
                    pass
                elif adaptation == 'launch_target_app' and value:
                    # Launch target application
                    pass
                # Add more adaptation implementations
                
        except Exception as e:
            self.logger.error(f"Failed to apply adaptations: {e}")
    
    def _record_execution_metrics(self, profile: AutomationProfile, 
                                result: ExecutionResult, insights: Dict[str, Any]):
        """Record execution metrics for analysis"""
        try:
            metrics = {
                'profile_name': profile.name,
                'execution_result': result.value,
                'timestamp': datetime.now().isoformat(),
                'insights': insights
            }
            
            # Store metrics (would integrate with metrics storage system)
            self.logger.debug(f"Recorded execution metrics: {metrics}")
            
        except Exception as e:
            self.logger.error(f"Failed to record metrics: {e}")
    
    def _analyze_optimal_timing(self, profile: AutomationProfile) -> Dict[str, Any]:
        """Analyze optimal timing for execution"""
        # Placeholder implementation
        return {
            'optimal_time': 'now',
            'confidence': 0.8,
            'factors': ['system_load', 'user_activity']
        }
    
    def _get_resource_optimization_suggestions(self, profile: AutomationProfile) -> List[Dict[str, Any]]:
        """Get resource optimization suggestions"""
        suggestions = []
        
        # Analyze profile complexity
        if len(profile.regions) > 20:
            suggestions.append({
                'type': 'optimization',
                'message': 'Consider splitting this profile into smaller profiles for better performance',
                'confidence': 0.7
            })
        
        if len(profile.rules) > 10:
            suggestions.append({
                'type': 'optimization',
                'message': 'Profile has many rules - consider using rule priorities for better control',
                'confidence': 0.8
            })
        
        return suggestions
    
    def _analyze_profile_structure(self, profile: AutomationProfile) -> Dict[str, Any]:
        """Analyze profile structure for optimization"""
        return {
            'region_count': len(profile.regions),
            'rule_count': len(profile.rules),
            'complexity_score': len(profile.regions) + len(profile.rules) * 2,
            'optimization_potential': 'medium'
        }
    
    def _analyze_execution_patterns(self, profile: AutomationProfile) -> Dict[str, Any]:
        """Analyze execution patterns"""
        # This would analyze historical execution data
        return {
            'average_execution_time': 30.0,
            'success_rate': 0.85,
            'common_failure_points': [],
            'optimization_opportunities': []
        }
    
    def _optimize_resource_usage(self, profile: AutomationProfile) -> Dict[str, Any]:
        """Optimize resource usage"""
        return {
            'memory_optimization': 'enabled',
            'cpu_optimization': 'enabled',
            'io_optimization': 'enabled'
        }
    
    def _optimize_execution_timing(self, profile: AutomationProfile) -> Dict[str, Any]:
        """Optimize execution timing"""
        return {
            'adaptive_delays': True,
            'smart_waiting': True,
            'parallel_execution': False  # Conservative default
        }