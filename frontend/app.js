const e = React.createElement;

function parseDiff(diff) {
    const lines = diff.split('\n');
    const parsedLines = [];

    let section = null;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        if (line.startsWith('File:') || line.startsWith('Function:')) {
            parsedLines.push({ type: 'context', content: line });
            section = null;
        } else if (line.trim() === 'Old Code:') {
            parsedLines.push({ type: 'context', content: 'Old Code:' });
            section = 'old';

            // Handle empty old code
            if (lines[i + 1]?.trim() === 'New Code:') {
                parsedLines.push({ type: 'old', content: '<NO PREVIOUS CODE>' });
            }
        } else if (line.trim() === 'New Code:') {
            parsedLines.push({ type: 'context', content: 'New Code:' });
            section = 'new';
        } else if (section === 'old' || section === 'new') {
            parsedLines.push({ type: section, content: line });
        } else {
            parsedLines.push({ type: 'context', content: line });
        }
    }

    return parsedLines;
}


// Analytics component to visualize PR data
function Analytics({ prs }) {
    // Count PRs by status
    const statusCounts = prs.reduce((acc, pr) => {
        acc[pr.status] = (acc[pr.status] || 0) + 1;
        return acc;
    }, {});

    // Count PRs by author
    const authorCounts = prs.reduce((acc, pr) => {
        acc[pr.author] = (acc[pr.author] || 0) + 1;
        return acc;
    }, {});

    // Calculate PRs over time (by month)
    const prsByMonth = prs.reduce((acc, pr) => {
        const date = new Date(pr.created_at);
        const monthYear = date.toLocaleString('default', { month: 'short', year: 'numeric' });
        acc[monthYear] = (acc[monthYear] || 0) + 1;
        return acc;
    }, {});

    // Create data arrays for charts
    const statusData = Object.entries(statusCounts).map(([status, count]) => ({
        status,
        count,
        color: status === 'Open' ? '#17a2b8' : 
               status === 'Merged' ? '#28a745' : 
               status === 'Closed' ? '#dc3545' : '#6c757d'
    }));

    const authorData = Object.entries(authorCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([author, count]) => ({ author, count }));

    const timelineData = Object.entries(prsByMonth)
        .sort((a, b) => new Date(a[0]) - new Date(b[0]))
        .map(([month, count]) => ({ month, count }));

    return e('div', { className: 'analytics-container' }, [
        e('h2', { key: 'title', className: 'analytics-title' }, 'Pull Request Analytics'),

        // Status distribution chart
        e('div', { key: 'status-chart', className: 'chart-container' }, [
            e('h3', { key: 'status-title' }, 'PR Status Distribution'),
            e('div', { key: 'status-bars', className: 'status-chart' }, 
                statusData.map(item => 
                    e('div', { key: item.status, className: 'status-bar-container' }, [
                        e('div', { key: 'label', className: 'status-label' }, `${item.status} (${item.count})`),
                        e('div', { key: 'bar-bg', className: 'status-bar-bg' }, 
                            e('div', { 
                                key: 'bar', 
                                className: 'status-bar', 
                                style: { 
                                    width: `${(item.count / prs.length) * 100}%`,
                                    backgroundColor: item.color
                                } 
                            })
                        )
                    ])
                )
            )
        ]),

        // Author contribution chart
        e('div', { key: 'author-chart', className: 'chart-container' }, [
            e('h3', { key: 'author-title' }, 'Top Contributors'),
            e('div', { key: 'author-bars', className: 'author-chart' }, 
                authorData.map(item => 
                    e('div', { key: item.author, className: 'author-bar-container' }, [
                        e('div', { key: 'label', className: 'author-label' }, [
                            e('img', { 
                                key: 'avatar', 
                                className: 'avatar', 
                                src: `https://ui-avatars.com/api/?name=${item.author}&size=24`, 
                                alt: item.author
                            }),
                            `${item.author} (${item.count})`
                        ]),
                        e('div', { key: 'bar-bg', className: 'author-bar-bg' }, 
                            e('div', { 
                                key: 'bar', 
                                className: 'author-bar', 
                                style: { 
                                    width: `${(item.count / Math.max(...Object.values(authorCounts))) * 100}%`
                                } 
                            })
                        )
                    ])
                )
            )
        ]),

        // Timeline chart
        e('div', { key: 'timeline-chart', className: 'chart-container' }, [
            e('h3', { key: 'timeline-title' }, 'PR Activity Over Time'),
            e('div', { key: 'timeline', className: 'timeline-chart' }, 
                timelineData.map((item, index) => 
                    e('div', { key: item.month, className: 'timeline-bar-container' }, [
                        e('div', { 
                            key: 'bar', 
                            className: 'timeline-bar', 
                            style: { 
                                height: `${(item.count / Math.max(...timelineData.map(d => d.count))) * 100}px`
                            } 
                        }),
                        e('div', { key: 'label', className: 'timeline-label' }, item.month)
                    ])
                )
            )
        ]),

        // Summary stats
        e('div', { key: 'summary-stats', className: 'summary-stats' }, [
            e('div', { key: 'total', className: 'stat-card' }, [
                e('h3', { key: 'title' }, 'Total PRs'),
                e('div', { key: 'value', className: 'stat-value' }, prs.length)
            ]),
            e('div', { key: 'open', className: 'stat-card' }, [
                e('h3', { key: 'title' }, 'Open PRs'),
                e('div', { key: 'value', className: 'stat-value' }, statusCounts['Open'] || 0)
            ]),
            e('div', { key: 'merged', className: 'stat-card' }, [
                e('h3', { key: 'title' }, 'Merged PRs'),
                e('div', { key: 'value', className: 'stat-value' }, statusCounts['Merged'] || 0)
            ]),
            e('div', { key: 'contributors', className: 'stat-card' }, [
                e('h3', { key: 'title' }, 'Contributors'),
                e('div', { key: 'value', className: 'stat-value' }, Object.keys(authorCounts).length)
            ])
        ])
    ]);
}

function renderDiffSection(diff) {
    const diffLines = parseDiff(diff);

    return React.createElement(
        'pre',
        { className: 'diff-content' },
        diffLines.map((line, index) => {
            const className =
                line.type === 'old' ? 'diff-old-code diff-code-line' :
                line.type === 'new' ? 'diff-new-code diff-code-line' :
                'diff-context-line';

            return React.createElement('div', { key: index, className }, line.content);
        })
    );
}

const ReactMarkdown = window.ReactMarkdown || (() => null) // fallback if not loaded


// Main App component
function App() {
    const [prs, setPrs] = React.useState([]);
    const [selectedPR, setSelectedPR] = React.useState(null);
    const [prDetails, setPRDetails] = React.useState(null);
    const [filter, setFilter] = React.useState("all");
    const [searchQuery, setSearchQuery] = React.useState("");
    const [isLoading, setIsLoading] = React.useState(true);
    const [showCommentForm, setShowCommentForm] = React.useState(false);
    const [comment, setComment] = React.useState("");
    const [comments, setComments] = React.useState([]);
    const [darkMode, setDarkMode] = React.useState(false);
    const [activeTab, setActiveTab] = React.useState("details"); // "details" or "analytics"

    React.useEffect(() => {
        setIsLoading(true);
        fetch('http://localhost:8000/api/prs')
            .then(res => res.json())
            .then(data => {
                setPrs(data);
                setIsLoading(false);
            })
            .catch(err => {
                console.error('Error fetching PRs:', err);
                setIsLoading(false);
            });
    }, []);

    React.useEffect(() => {
        // Apply dark mode class to body
        if (darkMode) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }, [darkMode]);

    const fetchDetails = (id) => {
        setIsLoading(true);
        fetch(`http://localhost:8000/api/prs/${id}`)
            .then(res => res.json())
            .then(data => {
                setPRDetails(data);
                setIsLoading(false);
                // Simulate fetching comments
                setComments([
                    { id: 1, author: "codereviewer", text: "Looks good to me!", timestamp: "2 hours ago" },
                    { id: 2, author: "securityexpert", text: "We should add input validation here.", timestamp: "1 hour ago" }
                ]);
            })
            .catch(err => {
                console.error('Error fetching PR details:', err);
                setIsLoading(false);
            });
    };

    const selectPR = (pr) => {
        setSelectedPR(pr);
        setActiveTab("details"); // Switch to details tab when selecting a PR
        fetchDetails(pr.id);
    };

    const handleAddComment = () => {
        if (comment.trim() === "") return;
        
        const newComment = {
            id: comments.length + 1,
            author: "you",
            text: comment,
            timestamp: "Just now"
        };
        
        setComments([...comments, newComment]);
        setComment("");
        setShowCommentForm(false);
    };

    const handleApprove = () => {
        alert("PR approved! (This would trigger an API call in production)");
    };

    const handleReject = () => {
        alert("PR rejected! (This would trigger an API call in production)");
    };

    // Function to switch to analytics tab
    const viewAnalytics = () => {
        setActiveTab("analytics");
    };

    // Filter PRs based on status and search query
    const filteredPRs = prs.filter(pr => {
        const matchesFilter = filter === "all" || pr.status === filter;
        const matchesSearch = pr.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                             pr.author.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFilter && matchesSearch;
    });

    // Create PR list items
    const prItems = filteredPRs.map(pr => 
        e('div', { 
            key: pr.id, 
            className: selectedPR && selectedPR.id === pr.id ? 'pr-item selected' : 'pr-item', 
            onClick: () => selectPR(pr) 
        }, [
            e('div', {key: 'pr-header', className: 'pr-header'}, [
                e('strong', {key: 'id'}, `#${pr.id}`),
                e('span', {
                    key: 'status',
                    className: `pr-status status-${pr.status}`
                }, pr.status)
            ]),
            e('div', {key: 'pr-title', className: 'pr-title'}, pr.title),
            e('div', {key: 'pr-meta', className: 'pr-meta'}, [
                e('span', {key: 'author'}, [
                    e('img', {key: 'avatar', className: 'avatar', src: `https://ui-avatars.com/api/?name=${pr.author}&size=24`, alt: pr.author}),
                    pr.author
                ]),
                e('span', {key: 'date', className: 'date'}, 'Updated: ' + (pr.updated_at || 'N/A'))
            ])
        ])
    );

    // Create filter controls
    const filterControls = e('div', {className: 'filter-controls'}, [
        e('div', {key: 'search', className: 'search-box'}, [
            e('input', {
                type: 'text',
                placeholder: 'Search PRs...',
                value: searchQuery,
                onChange: (e) => setSearchQuery(e.target.value),
                className: 'search-input'
            })
        ]),
        e('div', {key: 'filters', className: 'status-filters'}, [
            e('button', {
                className: filter === 'all' ? 'filter-btn active' : 'filter-btn',
                onClick: () => setFilter('all')
            }, 'All'),
            e('button', {
                className: filter === 'Open' ? 'filter-btn active' : 'filter-btn',
                onClick: () => setFilter('Open')
            }, 'Open'),
            e('button', {
                className: filter === 'Merged' ? 'filter-btn active' : 'filter-btn',
                onClick: () => setFilter('Merged')
            }, 'Merged'),
            e('button', {
                className: filter === 'Closed' ? 'filter-btn active' : 'filter-btn',
                onClick: () => setFilter('Closed')
            }, 'Closed')
        ])
    ]);

    // Create sidebar
    const sidebar = e('div', { className: 'sidebar' }, [
        e('div', {key: 'header', className: 'sidebar-header'}, [
            e('h2', {key: 'title'}, '📋 Pull Requests'),
            e('button', {
                key: 'theme-toggle',
                className: 'theme-toggle',
                onClick: () => setDarkMode(!darkMode)
            }, darkMode ? '☀️' : '🌙')
        ]),
        filterControls,
        e('div', {key: 'pr-list', className: 'pr-list'}, isLoading ? 
            e('div', {className: 'loading'}, 'Loading PRs...') : 
            prItems.length > 0 ? prItems : e('div', {className: 'no-results'}, 'No PRs match your filters'))
    ]);

    // Create tab navigation - show it regardless of whether a PR is selected
    const tabNav = e('div', {className: 'tab-navigation'}, [
        e('button', {
            key: 'details-tab',
            className: activeTab === 'details' ? 'tab-btn active' : 'tab-btn',
            onClick: () => setActiveTab('details'),
            disabled: !selectedPR
        }, 'PR Details'),
        e('button', {
            key: 'analytics-tab',
            className: activeTab === 'analytics' ? 'tab-btn active' : 'tab-btn',
            onClick: () => setActiveTab('analytics')
        }, 'Analytics')
    ]);

    // Create PR details content
    let prDetailsContent;
    if (isLoading && selectedPR) {
        prDetailsContent = e('div', {className: 'loading-container'}, [
            e('div', {key: 'spinner', className: 'loading-spinner'}),
            e('p', {key: 'text'}, 'Loading PR details...')
        ]);
    } else if (!prDetails && selectedPR) {
        prDetailsContent = e('p', null, 'No details available for this PR');
    } else if (selectedPR) {
        // PR details content
        const score = Number(prDetails.merge_confidence_score || 0); // 0-10
        const maxScore = 10;
        const percent = Math.min((score / maxScore) * 100, 100);
        const confidenceIndicator = e('div', { key: 'confidence-indicator', className: 'confidence-gradient-wrapper' }, [
            e('div', { className: 'confidence-gradient-bar' }, [
                e('div', {
                    className: 'confidence-score-indicator',
                    style: { left: `${percent}%` }
                })
            ]),
            e('div', { style: { marginTop: '8px', fontWeight: 600 } }, `Score: ${score}/10`)
        ]);
        
        // Comment section
        const commentList = comments.map(comment => 
            e('div', {key: `comment-${comment.id}`, className: 'comment'}, [
                e('div', {key: 'comment-header', className: 'comment-header'}, [
                    e('img', {key: 'avatar', className: 'avatar', src: `https://ui-avatars.com/api/?name=${comment.author}&size=32`, alt: comment.author}),
                    e('span', {key: 'author', className: 'comment-author'}, comment.author),
                    e('span', {key: 'time', className: 'comment-time'}, comment.timestamp)
                ]),
                e('div', {key: 'comment-body', className: 'comment-body'}, comment.text)
            ])
        );
        
        const commentSection = e('div', {key: 'comments', className: 'comments-section'}, [
            e('h3', {key: 'title'}, `Comments (${comments.length})`),
            ...commentList,
            showCommentForm ? 
                e('div', {key: 'comment-form', className: 'comment-form'}, [
                    e('textarea', {
                        key: 'textarea',
                        value: comment,
                        onChange: (e) => setComment(e.target.value),
                        placeholder: 'Add your comment...',
                        rows: 3
                    }),
                    e('div', {key: 'buttons', className: 'form-buttons'}, [
                        e('button', {
                            key: 'cancel',
                            className: 'cancel-btn',
                            onClick: () => {
                                setShowCommentForm(false);
                                setComment("");
                            }
                        }, 'Cancel'),
                        e('button', {
                            key: 'submit',
                            className: 'submit-btn',
                            onClick: handleAddComment
                        }, 'Submit')
                    ])
                ]) :
                e('button', {
                    key: 'add-comment',
                    className: 'add-comment-btn',
                    onClick: () => setShowCommentForm(true)
                }, '+ Add Comment')
        ]);
        
        // Action buttons with added View Analytics button
        const actionButtons = e('div', {key: 'actions', className: 'action-buttons'}, [
            e('button', {
                key: 'approve',
                className: 'approve-btn',
                onClick: handleApprove
            }, 'Approve PR'),
            e('button', {
                key: 'reject',
                className: 'reject-btn',
                onClick: handleReject
            }, 'Request Changes'),
            e('button', {
                key: 'view-analytics',
                className: 'view-analytics-btn',
                onClick: viewAnalytics
            }, 'View Analytics')
        ]);
        
        // PR Details Tab Content
        prDetailsContent = e(React.Fragment, null, [
            e('div', {key: 'pr-header', className: 'pr-detail-header'}, [
                e('h2', {key: 'title'}, `#${selectedPR.id} - ${selectedPR.title}`),
                e('div', {key: 'meta', className: 'pr-meta-details'}, [
                    e('span', {key: 'status', className: `status-badge status-${selectedPR.status}`}, selectedPR.status),
                    e('span', {key: 'author'}, [
                        e('img', {key: 'avatar', className: 'avatar', src: `https://ui-avatars.com/api/?name=${selectedPR.author}&size=24`, alt: selectedPR.author}),
                        `Author: ${selectedPR.author}`
                    ]),
                    // Add a "View Analytics" button in the header too
                    e('button', {
                        key: 'header-view-analytics',
                        className: 'header-view-analytics-btn',
                        onClick: viewAnalytics
                    }, 'View Analytics')
                ])
            ]),
            
            e('div', {key: 'pr-body', className: 'pr-detail-body'}, [
                e('div', {key: 'summary', className: 'ai-summary'}, [
                    e('h3', {key: 'title'}, 'AI Summary'),
                    e('p', {key: 'text'}, prDetails.ai_summary)
                ]),
                
                e('div', {key: 'confidence', className: 'confidence-section'}, [
                    e('h3', {key: 'title'}, 'Merge Confidence'),
                    confidenceIndicator
                ]),
                
                e('div', {key: 'quality', className: 'code-quality'}, [
                    e('h3', {key: 'title'}, 'Code Quality Assessment'),
                    e('pre', {key: 'text'}, prDetails.code_quality)
                ]),
                
                
                ('div', {key: 'doc-string', className: 'doc-string-section'}, [
                    e('h3', {key: 'title'}, 'Documentation'),
                    e('div', {key: 'content', className: 'doc-string-content'},
                        e(ReactMarkdown, null, prDetails.doc_string || 'No documentation available for this PR.')
                    )
                ]),

                e('div', {key: 'diff', className: 'diff-section'}, [
                    e('h3', {key: 'title'}, 'Diff'),
                    renderDiffSection(prDetails.diff)
                ]),
                
                commentSection,
                
                actionButtons
            ])
        ]);
    }

    // Create main content based on active tab
    let mainContent;
    if (activeTab === 'details' && !selectedPR) {
        mainContent = e('div', {className: 'empty-state'}, [
            e('h2', {key: 'title'}, 'Pull Request Dashboard'),
            e('p', {key: 'subtitle'}, 'Select a PR from the sidebar or view PR Analytics'),
            e('button', {
                key: 'view-analytics',
                className: 'view-analytics-btn',
                onClick: () => setActiveTab('analytics')
            }, 'View Analytics')
        ]);
    } else if (activeTab === 'details' && selectedPR) {
        // Show PR details tab
        mainContent = prDetailsContent;
    } else if (activeTab === 'analytics') {
        // Show Analytics tab
        mainContent = e(Analytics, { prs: prs });
    }

    const main = e('div', { className: 'main' }, [
        tabNav,
        mainContent
    ]);

    // Render the full container
    return e('div', { className: 'container' }, [sidebar, main]);
}

// Render the App
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(e(App));